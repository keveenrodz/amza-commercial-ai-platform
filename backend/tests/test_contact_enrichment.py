"""
Cubre spec 013 (Contact Enrichment & Follow-ups):

1. Agregar/quitar una etiqueta es idempotente.
2. Alternar favorito invierte el valor cada vez.
3. Agregar una nota y listarlas devuelve el nombre del autor correcto, en orden cronológico.
4. Programar un seguimiento con uno ya activo -> 422.
5. Resolver un seguimiento sin ninguno activo -> 404.
6. Resolver un seguimiento activo y volver a listar oportunidades -> ya no aparece en follow_up.
7. ReceiveIncomingMessageUseCase marca has_unread_messages=True en un mensaje entrante nuevo.
8. GetConversationHistoryUseCase marca has_unread_messages=False tras leer una conversación.
9. POST .../assign-advisor reasigna correctamente de un asesor a otro.
10. GET .../advisors devuelve solo asesores activos con rol Advisor, ordenados por nombre.
11. GET .../opportunities/search?q=... encuentra por nombre de contacto y por mensaje.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from httpx import AsyncClient
from sqlalchemy import select

from app.services.conversation_context_assembler import ConversationContextAssembler
from app.services.conversation_summarization_service import ConversationSummarizationService
from app.use_cases.receive_incoming_message import (
    IncomingMessageInput,
    ReceiveIncomingMessageUseCase,
)
from core.entities.contact import Contact
from core.entities.message import Message
from core.enums.channel import ChannelType
from core.enums.message import MessageContentType
from core.interfaces.providers import CompletionRequest, ConversationContext
from core.value_objects.identifiers import AgentId
from infrastructure.database.session import AsyncSessionFactory
from modules.agents.models.agent import AgentModel
from modules.configuration.models.organization import OrganizationModel
from modules.opportunities.models.contact import ContactModel
from modules.opportunities.models.conversation import ConversationModel
from modules.opportunities.models.message import MessageModel
from modules.opportunities.models.opportunity import OpportunityModel
from scripts.create_user import create_user
from tests.test_security_and_identity import _ORG_SLUG, _login, _seed_organization


class _FakeAIProvider:
    async def generate(self, context: ConversationContext, agent_id: AgentId) -> str:
        return "Respuesta automática de prueba"

    async def complete(self, request: CompletionRequest) -> str:
        return "resumen"

    async def health(self) -> bool:
        return True


class _FakeChannelProvider:
    async def send(self, message: Message, contact: Contact) -> None:
        return None

    async def health(self) -> bool:
        return True


async def _seed_opportunity_with_contact(
    *,
    organization_slug: str,
    display_name: str,
    assigned_advisor_id: uuid.UUID | None = None,
) -> tuple[uuid.UUID, uuid.UUID]:
    async with AsyncSessionFactory() as session:
        org = (
            await session.execute(
                select(OrganizationModel).where(OrganizationModel.slug == organization_slug)
            )
        ).scalar_one()

        now = datetime.now(tz=UTC)

        agent_id = uuid.uuid4()
        session.add(
            AgentModel(
                id=agent_id,
                organization_id=org.id,
                name="Test Agent",
                system_prompt="You are a helpful assistant.",
                model="openai/gpt-4.1-nano",
                status="active",
                created_at=now,
                updated_at=now,
            )
        )

        contact_id = uuid.uuid4()
        session.add(
            ContactModel(
                id=contact_id,
                organization_id=org.id,
                external_id=str(uuid.uuid4()),
                channel_type="telegram",
                display_name=display_name,
                status="active",
                created_at=now,
                updated_at=now,
            )
        )

        opportunity_id = uuid.uuid4()
        session.add(
            OpportunityModel(
                id=opportunity_id,
                organization_id=org.id,
                contact_id=contact_id,
                agent_id=agent_id,
                assigned_advisor_id=assigned_advisor_id,
                status="qualified" if assigned_advisor_id is None else "waiting_for_advisor",
                attention_mode="ai" if assigned_advisor_id is None else "human",
                channel_type="telegram",
                started_at=now,
                last_activity_at=now,
                closed_at=None,
            )
        )
        session.add(
            ConversationModel(
                id=uuid.uuid4(),
                opportunity_id=opportunity_id,
                started_at=now,
                ended_at=None,
            )
        )

        await session.commit()
        return opportunity_id, contact_id


async def test_add_and_remove_tag_is_idempotent(client: AsyncClient) -> None:
    await _seed_organization()
    await create_user(_ORG_SLUG, "juan@gmail.com", "Juan Perez", "advisor")
    await _login(client, "juan@gmail.com")

    _, contact_id = await _seed_opportunity_with_contact(
        organization_slug=_ORG_SLUG, display_name="Cliente Uno"
    )

    tags_url = f"/organizations/{_ORG_SLUG}/contacts/{contact_id}/tags"
    r1 = await client.post(tags_url, json={"tag": "VIP"})
    assert r1.status_code == 200, r1.text
    assert r1.json()["tags"] == ["VIP"]

    r2 = await client.post(tags_url, json={"tag": "VIP"})
    assert r2.json()["tags"] == ["VIP"]  # no se duplica

    r3 = await client.delete(f"/organizations/{_ORG_SLUG}/contacts/{contact_id}/tags/VIP")
    assert r3.json()["tags"] == []

    r4 = await client.delete(f"/organizations/{_ORG_SLUG}/contacts/{contact_id}/tags/VIP")
    assert r4.status_code == 200  # quitar una que no existe no lanza error
    assert r4.json()["tags"] == []


async def test_toggle_favorite_inverts_each_time(client: AsyncClient) -> None:
    await _seed_organization()
    await create_user(_ORG_SLUG, "juan@gmail.com", "Juan Perez", "advisor")
    await _login(client, "juan@gmail.com")

    _, contact_id = await _seed_opportunity_with_contact(
        organization_slug=_ORG_SLUG, display_name="Cliente Dos"
    )

    r1 = await client.post(f"/organizations/{_ORG_SLUG}/contacts/{contact_id}/favorite")
    assert r1.json()["is_favorite"] is True

    r2 = await client.post(f"/organizations/{_ORG_SLUG}/contacts/{contact_id}/favorite")
    assert r2.json()["is_favorite"] is False


async def test_add_note_and_list_returns_author_name_in_order(client: AsyncClient) -> None:
    await _seed_organization()
    await create_user(_ORG_SLUG, "juan@gmail.com", "Juan Perez", "advisor")
    await create_user(_ORG_SLUG, "andrea@gmail.com", "Andrea Torres", "advisor")
    await _login(client, "juan@gmail.com")
    juan_id = (await client.get("/auth/me")).json()["id"]
    advisors = (await client.get(f"/organizations/{_ORG_SLUG}/advisors")).json()
    andrea_id = next(a["id"] for a in advisors if a["full_name"] == "Andrea Torres")

    _, contact_id = await _seed_opportunity_with_contact(
        organization_slug=_ORG_SLUG, display_name="Cliente Tres"
    )

    r1 = await client.post(
        f"/organizations/{_ORG_SLUG}/contacts/{contact_id}/notes",
        json={"advisor_id": juan_id, "content": "Primera nota"},
    )
    assert r1.status_code == 200, r1.text
    assert r1.json()["author_name"] == "Juan Perez"

    r2 = await client.post(
        f"/organizations/{_ORG_SLUG}/contacts/{contact_id}/notes",
        json={"advisor_id": andrea_id, "content": "Segunda nota"},
    )
    assert r2.json()["author_name"] == "Andrea Torres"

    listed = (await client.get(f"/organizations/{_ORG_SLUG}/contacts/{contact_id}/notes")).json()
    assert len(listed) == 2
    assert [n["author_name"] for n in listed] == ["Juan Perez", "Andrea Torres"]
    assert [n["content"] for n in listed] == ["Primera nota", "Segunda nota"]


async def test_schedule_follow_up_with_one_already_active_returns_422(client: AsyncClient) -> None:
    await _seed_organization()
    await create_user(_ORG_SLUG, "juan@gmail.com", "Juan Perez", "advisor")
    await _login(client, "juan@gmail.com")
    advisor_id = (await client.get("/auth/me")).json()["id"]

    opportunity_id, _ = await _seed_opportunity_with_contact(
        organization_slug=_ORG_SLUG, display_name="Cliente Cuatro"
    )

    follow_up_url = f"/organizations/{_ORG_SLUG}/opportunities/{opportunity_id}/follow-up"
    body = {
        "advisor_id": advisor_id,
        "due_at": "2026-09-01T10:00:00Z",
        "reason": "Confirmar pedido",
    }
    r1 = await client.post(follow_up_url, json=body)
    assert r1.status_code == 200, r1.text

    r2 = await client.post(follow_up_url, json=body)
    assert r2.status_code == 422


async def test_resolve_follow_up_without_active_returns_404(client: AsyncClient) -> None:
    await _seed_organization()
    await create_user(_ORG_SLUG, "juan@gmail.com", "Juan Perez", "advisor")
    await _login(client, "juan@gmail.com")

    opportunity_id, _ = await _seed_opportunity_with_contact(
        organization_slug=_ORG_SLUG, display_name="Cliente Cinco"
    )

    response = await client.post(
        f"/organizations/{_ORG_SLUG}/opportunities/{opportunity_id}/follow-up/resolve"
    )
    assert response.status_code == 404


async def test_resolve_follow_up_removes_it_from_opportunity_list(client: AsyncClient) -> None:
    await _seed_organization()
    await create_user(_ORG_SLUG, "juan@gmail.com", "Juan Perez", "advisor")
    await _login(client, "juan@gmail.com")
    advisor_id = (await client.get("/auth/me")).json()["id"]

    opportunity_id, _ = await _seed_opportunity_with_contact(
        organization_slug=_ORG_SLUG, display_name="Cliente Seis"
    )

    await client.post(
        f"/organizations/{_ORG_SLUG}/opportunities/{opportunity_id}/follow-up",
        json={"advisor_id": advisor_id, "due_at": "2026-09-01T10:00:00Z", "reason": "Seguimiento"},
    )

    listing_before = await client.get(f"/organizations/{_ORG_SLUG}/opportunities")
    item_before = next(
        i for i in listing_before.json() if i["opportunity"]["id"] == str(opportunity_id)
    )
    assert item_before["follow_up"] is not None

    resolve = await client.post(
        f"/organizations/{_ORG_SLUG}/opportunities/{opportunity_id}/follow-up/resolve"
    )
    assert resolve.status_code == 200

    listing_after = await client.get(f"/organizations/{_ORG_SLUG}/opportunities")
    item_after = next(
        i for i in listing_after.json() if i["opportunity"]["id"] == str(opportunity_id)
    )
    assert item_after["follow_up"] is None


async def test_receive_incoming_message_marks_opportunity_unread() -> None:
    await _seed_organization()

    async with AsyncSessionFactory() as session:
        org = (
            await session.execute(
                select(OrganizationModel).where(OrganizationModel.slug == _ORG_SLUG)
            )
        ).scalar_one()
        now = datetime.now(tz=UTC)
        session.add(
            AgentModel(
                id=uuid.uuid4(),
                organization_id=org.id,
                name="Test Agent",
                system_prompt="You are a helpful assistant.",
                model="openai/gpt-4.1-nano",
                status="active",
                created_at=now,
                updated_at=now,
            )
        )
        await session.commit()

    use_case = ReceiveIncomingMessageUseCase(
        session_factory=AsyncSessionFactory,
        ai_provider=_FakeAIProvider(),
        channel_provider=_FakeChannelProvider(),
        context_assembler=ConversationContextAssembler(working_memory_size=10),
        summarization_service=ConversationSummarizationService(
            ai_provider=_FakeAIProvider(),
            summarization_model="openai/gpt-4.1-nano",
        ),
        summary_trigger_messages=999,
    )

    opportunity = await use_case.execute(
        IncomingMessageInput(
            organization_slug=_ORG_SLUG,
            channel_type=ChannelType.TELEGRAM,
            external_contact_id="chat-123",
            contact_display_name="Cliente Siete",
            content="Hola, necesito información",
            content_type=MessageContentType.TEXT,
        )
    )

    assert opportunity.has_unread_messages is True


async def test_get_conversation_history_marks_opportunity_read(client: AsyncClient) -> None:
    await _seed_organization()
    await create_user(_ORG_SLUG, "juan@gmail.com", "Juan Perez", "advisor")
    await _login(client, "juan@gmail.com")

    opportunity_id, _ = await _seed_opportunity_with_contact(
        organization_slug=_ORG_SLUG, display_name="Cliente Ocho"
    )

    async with AsyncSessionFactory() as session:
        model = (
            await session.execute(
                select(OpportunityModel).where(OpportunityModel.id == opportunity_id)
            )
        ).scalar_one()
        model.has_unread_messages = True
        await session.commit()

    response = await client.get(
        f"/organizations/{_ORG_SLUG}/opportunities/{opportunity_id}/history"
    )
    assert response.status_code == 200, response.text
    assert response.json()["opportunity"]["has_unread_messages"] is False

    async with AsyncSessionFactory() as session:
        model = (
            await session.execute(
                select(OpportunityModel).where(OpportunityModel.id == opportunity_id)
            )
        ).scalar_one()
        assert model.has_unread_messages is False


async def test_assign_advisor_reassigns_from_one_advisor_to_another(client: AsyncClient) -> None:
    await _seed_organization()
    await create_user(_ORG_SLUG, "juan@gmail.com", "Juan Perez", "advisor")
    await create_user(_ORG_SLUG, "andrea@gmail.com", "Andrea Torres", "advisor")
    await _login(client, "juan@gmail.com")
    juan_id = (await client.get("/auth/me")).json()["id"]

    andrea_id = (
        await client.get(f"/organizations/{_ORG_SLUG}/advisors")
    ).json()
    andrea_id = next(a["id"] for a in andrea_id if a["full_name"] == "Andrea Torres")

    opportunity_id, _ = await _seed_opportunity_with_contact(
        organization_slug=_ORG_SLUG,
        display_name="Cliente Nueve",
        assigned_advisor_id=uuid.UUID(juan_id),
    )

    response = await client.post(
        f"/organizations/{_ORG_SLUG}/opportunities/{opportunity_id}/assign-advisor",
        json={"advisor_id": andrea_id},
    )
    assert response.status_code == 200, response.text
    assert response.json()["assigned_advisor_id"] == andrea_id


async def test_list_advisors_returns_only_active_advisors_ordered_by_name(
    client: AsyncClient,
) -> None:
    await _seed_organization()
    await create_user(_ORG_SLUG, "zeta@gmail.com", "Zeta Asesor", "advisor")
    await create_user(_ORG_SLUG, "alfa@gmail.com", "Alfa Asesor", "advisor")
    await create_user(_ORG_SLUG, "admin@gmail.com", "Admin Principal", "administrator")
    await _login(client, "zeta@gmail.com")

    response = await client.get(f"/organizations/{_ORG_SLUG}/advisors")
    assert response.status_code == 200, response.text
    names = [a["full_name"] for a in response.json()]
    assert names == ["Alfa Asesor", "Zeta Asesor"]  # alfabético, sin el administrator


async def test_search_opportunities_by_contact_name_and_message_content(
    client: AsyncClient,
) -> None:
    await _seed_organization()
    await create_user(_ORG_SLUG, "juan@gmail.com", "Juan Perez", "advisor")
    await _login(client, "juan@gmail.com")

    opp_id_1, _ = await _seed_opportunity_with_contact(
        organization_slug=_ORG_SLUG, display_name="Distribuidora El Roble"
    )
    opp_id_2, _ = await _seed_opportunity_with_contact(
        organization_slug=_ORG_SLUG, display_name="Empaques del Valle"
    )

    async with AsyncSessionFactory() as session:
        conversation = (
            await session.execute(
                select(ConversationModel).where(ConversationModel.opportunity_id == opp_id_2)
            )
        ).scalar_one()
        session.add(
            MessageModel(
                id=uuid.uuid4(),
                conversation_id=conversation.id,
                sender_role="user",
                content_type="text",
                content="necesito cajas corrugadas urgente",
                channel_type="telegram",
                sent_at=datetime.now(tz=UTC),
            )
        )
        await session.commit()

    search_url = f"/organizations/{_ORG_SLUG}/opportunities/search"
    by_name = await client.get(search_url, params={"q": "roble"})
    assert by_name.status_code == 200, by_name.text
    assert [i["opportunity"]["id"] for i in by_name.json()] == [str(opp_id_1)]

    by_message = await client.get(search_url, params={"q": "corrugadas"})
    assert [i["opportunity"]["id"] for i in by_message.json()] == [str(opp_id_2)]
