"""
Cubre el feedback del usuario tras validar specs 013/013b/014 en el navegador (no una spec nueva,
refinamientos directos sobre lo ya implementado):

1. Tomar una conversación desde la IA deja una nota de sistema en el hilo.
2. Reasignar de un asesor a otro deja una nota de sistema con ambos nombres.
3. Devolver a IA deja una nota de sistema con el nombre de quien la tenía asignada.
4. Programar y resolver un seguimiento dejan cada uno su propia nota de sistema.
5. Opportunity.unread_count es un conteo real (no un booleano) -- sube uno por cada mensaje
   entrante nuevo mientras nadie la ha vuelto a abrir.
6. El listado de oportunidades abiertas incluye una vista previa del último mensaje, truncada si
   es texto largo, y con una etiqueta legible si no es texto.
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
from core.enums.channel import ChannelType
from core.enums.message import MessageContentType, MessageRole
from infrastructure.database.session import AsyncSessionFactory
from modules.agents.models.agent import AgentModel
from modules.configuration.models.organization import OrganizationModel
from modules.opportunities.models.conversation import ConversationModel
from modules.opportunities.models.message import MessageModel
from scripts.create_user import create_user
from tests.test_contact_enrichment import (
    _FakeAIProvider,
    _FakeChannelProvider,
    _seed_opportunity_with_contact,
)
from tests.test_security_and_identity import _ORG_SLUG, _login, _seed_organization


async def _last_message(client: AsyncClient, opportunity_id: object) -> dict:
    history = await client.get(
        f"/organizations/{_ORG_SLUG}/opportunities/{opportunity_id}/history"
    )
    messages = history.json()["messages"]
    assert messages, "se esperaba al menos un mensaje (la nota de sistema)"
    return messages[-1]


async def _get_conversation_id(opportunity_id: uuid.UUID) -> uuid.UUID:
    async with AsyncSessionFactory() as session:
        conversation = (
            await session.execute(
                select(ConversationModel).where(
                    ConversationModel.opportunity_id == opportunity_id
                )
            )
        ).scalar_one()
        return conversation.id


async def _add_message(conversation_id: uuid.UUID, content: str, content_type: str) -> None:
    async with AsyncSessionFactory() as session:
        session.add(
            MessageModel(
                id=uuid.uuid4(),
                conversation_id=conversation_id,
                sender_role="user",
                content_type=content_type,
                content=content,
                channel_type="telegram",
                sent_at=datetime.now(tz=UTC),
            )
        )
        await session.commit()


async def _seed_agent(organization_slug: str) -> None:
    async with AsyncSessionFactory() as session:
        org = (
            await session.execute(
                select(OrganizationModel).where(OrganizationModel.slug == organization_slug)
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


def _make_receive_use_case() -> ReceiveIncomingMessageUseCase:
    return ReceiveIncomingMessageUseCase(
        session_factory=AsyncSessionFactory,
        ai_provider=_FakeAIProvider(),
        channel_provider=_FakeChannelProvider(),
        context_assembler=ConversationContextAssembler(working_memory_size=10),
        summarization_service=ConversationSummarizationService(
            ai_provider=_FakeAIProvider(), summarization_model="openai/gpt-4.1-nano",
        ),
        summary_trigger_messages=999,
    )


async def test_taking_from_ai_records_system_message(client: AsyncClient) -> None:
    await _seed_organization()
    await create_user(_ORG_SLUG, "juan@gmail.com", "Juan Perez", "advisor")
    await _login(client, "juan@gmail.com")
    juan_id = (await client.get("/auth/me")).json()["id"]

    opportunity_id, _ = await _seed_opportunity_with_contact(
        organization_slug=_ORG_SLUG, display_name="Cliente A",
    )

    response = await client.post(
        f"/organizations/{_ORG_SLUG}/opportunities/{opportunity_id}/assign-advisor",
        json={"advisor_id": juan_id},
    )
    assert response.status_code == 200, response.text

    last = await _last_message(client, opportunity_id)
    assert last["sender_role"] == MessageRole.SYSTEM.value
    assert "Juan Perez" in last["content"]
    assert "tomó esta conversación" in last["content"]


async def test_reassign_records_system_message_with_both_names(client: AsyncClient) -> None:
    await _seed_organization()
    await create_user(_ORG_SLUG, "juan@gmail.com", "Juan Perez", "advisor")
    await create_user(_ORG_SLUG, "andrea@gmail.com", "Andrea Torres", "advisor")
    await _login(client, "juan@gmail.com")
    juan_id = (await client.get("/auth/me")).json()["id"]
    advisors = (await client.get(f"/organizations/{_ORG_SLUG}/advisors")).json()
    andrea_id = next(a["id"] for a in advisors if a["full_name"] == "Andrea Torres")

    opportunity_id, _ = await _seed_opportunity_with_contact(
        organization_slug=_ORG_SLUG,
        display_name="Cliente B",
        assigned_advisor_id=uuid.UUID(juan_id),
    )

    response = await client.post(
        f"/organizations/{_ORG_SLUG}/opportunities/{opportunity_id}/assign-advisor",
        json={"advisor_id": andrea_id},
    )
    assert response.status_code == 200, response.text

    last = await _last_message(client, opportunity_id)
    assert last["sender_role"] == MessageRole.SYSTEM.value
    assert "Juan Perez" in last["content"]
    assert "Andrea Torres" in last["content"]


async def test_return_to_ai_records_system_message(client: AsyncClient) -> None:
    await _seed_organization()
    await create_user(_ORG_SLUG, "juan@gmail.com", "Juan Perez", "advisor")
    await _login(client, "juan@gmail.com")
    juan_id = (await client.get("/auth/me")).json()["id"]

    opportunity_id, _ = await _seed_opportunity_with_contact(
        organization_slug=_ORG_SLUG,
        display_name="Cliente C",
        assigned_advisor_id=uuid.UUID(juan_id),
    )

    response = await client.post(
        f"/organizations/{_ORG_SLUG}/opportunities/{opportunity_id}/return-to-ai"
    )
    assert response.status_code == 200, response.text

    last = await _last_message(client, opportunity_id)
    assert last["sender_role"] == MessageRole.SYSTEM.value
    assert "Juan Perez" in last["content"]
    assert "devolvió la conversación a la IA" in last["content"]


async def test_schedule_and_resolve_follow_up_record_system_messages(
    client: AsyncClient,
) -> None:
    await _seed_organization()
    await create_user(_ORG_SLUG, "juan@gmail.com", "Juan Perez", "advisor")
    await _login(client, "juan@gmail.com")
    juan_id = (await client.get("/auth/me")).json()["id"]

    opportunity_id, _ = await _seed_opportunity_with_contact(
        organization_slug=_ORG_SLUG, display_name="Cliente D",
    )

    schedule = await client.post(
        f"/organizations/{_ORG_SLUG}/opportunities/{opportunity_id}/follow-up",
        json={"advisor_id": juan_id, "due_at": "2099-01-15T14:00:00Z", "reason": "Confirmar"},
    )
    assert schedule.status_code == 200, schedule.text

    after_schedule = await _last_message(client, opportunity_id)
    assert after_schedule["sender_role"] == MessageRole.SYSTEM.value
    assert "Juan Perez" in after_schedule["content"]
    assert "programó un seguimiento" in after_schedule["content"]

    resolve = await client.post(
        f"/organizations/{_ORG_SLUG}/opportunities/{opportunity_id}/follow-up/resolve",
        json={"advisor_id": juan_id},
    )
    assert resolve.status_code == 200, resolve.text

    after_resolve = await _last_message(client, opportunity_id)
    assert after_resolve["sender_role"] == MessageRole.SYSTEM.value
    assert "marcó el seguimiento de este cliente como resuelto" in after_resolve["content"]


async def test_unread_count_is_a_real_count() -> None:
    await _seed_organization()
    await _seed_agent(_ORG_SLUG)

    use_case = _make_receive_use_case()
    input_data = IncomingMessageInput(
        organization_slug=_ORG_SLUG,
        channel_type=ChannelType.TELEGRAM,
        external_contact_id="chat-unread-count",
        contact_display_name="Cliente Contador",
        content="Primer mensaje",
        content_type=MessageContentType.TEXT,
    )
    opportunity = await use_case.execute(input_data)
    assert opportunity.unread_count == 1

    opportunity = await use_case.execute(
        IncomingMessageInput(
            organization_slug=_ORG_SLUG,
            channel_type=ChannelType.TELEGRAM,
            external_contact_id="chat-unread-count",
            contact_display_name="Cliente Contador",
            content="Segundo mensaje",
            content_type=MessageContentType.TEXT,
        )
    )
    assert opportunity.unread_count == 2


async def test_last_message_preview_appears_in_open_opportunities_list(
    client: AsyncClient,
) -> None:
    await _seed_organization()
    await create_user(_ORG_SLUG, "juan@gmail.com", "Juan Perez", "advisor")
    await _login(client, "juan@gmail.com")

    opportunity_id, _ = await _seed_opportunity_with_contact(
        organization_slug=_ORG_SLUG, display_name="Cliente F",
    )
    conversation_id = await _get_conversation_id(opportunity_id)
    await _add_message(
        conversation_id,
        "Necesito una cotización para 500 cajas de cartón corrugado urgente",
        "text",
    )

    response = await client.get(f"/organizations/{_ORG_SLUG}/opportunities")
    assert response.status_code == 200, response.text
    item = next(i for i in response.json() if i["opportunity"]["id"] == str(opportunity_id))
    assert item["last_message_preview"] is not None
    assert item["last_message_preview"].startswith("Necesito una cotización")
    assert len(item["last_message_preview"]) <= 61  # 60 chars + "…"


async def test_last_message_preview_for_non_text_shows_friendly_label(
    client: AsyncClient,
) -> None:
    await _seed_organization()
    await create_user(_ORG_SLUG, "juan@gmail.com", "Juan Perez", "advisor")
    await _login(client, "juan@gmail.com")

    opportunity_id, _ = await _seed_opportunity_with_contact(
        organization_slug=_ORG_SLUG, display_name="Cliente G",
    )
    conversation_id = await _get_conversation_id(opportunity_id)
    await _add_message(conversation_id, "https://example.com/foto.jpg", "image")

    response = await client.get(f"/organizations/{_ORG_SLUG}/opportunities")
    item = next(i for i in response.json() if i["opportunity"]["id"] == str(opportunity_id))
    assert item["last_message_preview"] == "📷 Imagen"
