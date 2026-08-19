"""
Cubre spec 012 (Chat Panel Redesign), sección 1 -- corrección de contrato:

1. ContactRepository.list_by_ids: lista vacía -> [] sin consultar; ids existentes -> Contacts.
2. GET /organizations/{slug}/opportunities incluye contact.display_name correcto.
3. GET .../opportunities/{id}/history incluye contact con el display_name correcto.
4. Regresión: assign-advisor/return-to-ai/messages no ganan ningún campo de contacto -- su shape
   de respuesta no debería haber cambiado al tocar OpportunityResponse.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from httpx import AsyncClient

from app.dependencies import get_send_advisor_reply_use_case
from app.use_cases.send_advisor_reply import SendAdvisorReplyUseCase
from core.entities.contact import Contact
from core.entities.message import Message
from core.value_objects.identifiers import ContactId
from infrastructure.database.session import AsyncSessionFactory
from modules.agents.models.agent import AgentModel
from modules.configuration.models.organization import OrganizationModel
from modules.opportunities.models.contact import ContactModel
from modules.opportunities.models.conversation import ConversationModel
from modules.opportunities.models.opportunity import OpportunityModel
from modules.opportunities.repositories.contact import SQLAlchemyContactRepository
from scripts.create_user import create_user
from tests.test_security_and_identity import _ORG_SLUG, _login, _seed_organization


class _SpyChannelProvider:
    async def send(self, message: Message, contact: Contact) -> None:
        return None

    async def health(self) -> bool:
        return True


async def _seed_opportunity_with_contact(
    *,
    organization_slug: str,
    display_name: str,
    phone_number: str | None = None,
) -> tuple[uuid.UUID, uuid.UUID]:
    from sqlalchemy import select

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
                phone_number=phone_number,
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
                assigned_advisor_id=None,
                status="qualified",
                attention_mode="ai",
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


async def test_contact_repository_list_by_ids_empty_returns_empty_list() -> None:
    async with AsyncSessionFactory() as session:
        repo = SQLAlchemyContactRepository(session)
        assert await repo.list_by_ids([]) == []


async def test_contact_repository_list_by_ids_returns_matching_contacts() -> None:
    await _seed_organization()
    _, contact_id = await _seed_opportunity_with_contact(
        organization_slug=_ORG_SLUG,
        display_name="Distribuidora El Roble",
    )

    async with AsyncSessionFactory() as session:
        repo = SQLAlchemyContactRepository(session)
        contacts = await repo.list_by_ids([ContactId.from_string(str(contact_id))])

    assert len(contacts) == 1
    assert contacts[0].display_name == "Distribuidora El Roble"


async def test_list_opportunities_includes_contact_display_name(client: AsyncClient) -> None:
    await _seed_organization()
    await create_user(_ORG_SLUG, "juan@gmail.com", "Juan Perez", "advisor")
    await _login(client, "juan@gmail.com")

    await _seed_opportunity_with_contact(
        organization_slug=_ORG_SLUG,
        display_name="Litoempaques S.A.S.",
        phone_number="+57 300 000 0000",
    )

    response = await client.get(f"/organizations/{_ORG_SLUG}/opportunities")

    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body) == 1
    assert body[0]["contact"]["display_name"] == "Litoempaques S.A.S."
    assert body[0]["contact"]["phone_number"] == "+57 300 000 0000"
    assert "id" in body[0]["opportunity"]


async def test_conversation_history_includes_contact(client: AsyncClient) -> None:
    await _seed_organization()
    await create_user(_ORG_SLUG, "juan@gmail.com", "Juan Perez", "advisor")
    await _login(client, "juan@gmail.com")

    opportunity_id, _ = await _seed_opportunity_with_contact(
        organization_slug=_ORG_SLUG,
        display_name="Empaques del Valle",
    )

    response = await client.get(
        f"/organizations/{_ORG_SLUG}/opportunities/{opportunity_id}/history"
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["contact"]["display_name"] == "Empaques del Valle"


async def test_mutation_endpoints_response_shape_unchanged(client: AsyncClient) -> None:
    from app.main import app

    await _seed_organization()
    await create_user(_ORG_SLUG, "juan@gmail.com", "Juan Perez", "advisor")
    await _login(client, "juan@gmail.com")
    advisor_id = (await client.get("/auth/me")).json()["id"]

    opportunity_id, _ = await _seed_opportunity_with_contact(
        organization_slug=_ORG_SLUG,
        display_name="Comercial Andina",
    )

    app.dependency_overrides[get_send_advisor_reply_use_case] = (
        lambda: SendAdvisorReplyUseCase(
            session_factory=AsyncSessionFactory,
            channel_provider=_SpyChannelProvider(),
        )
    )

    assign_response = await client.post(
        f"/organizations/{_ORG_SLUG}/opportunities/{opportunity_id}/assign-advisor",
        json={"advisor_id": advisor_id},
    )
    assert assign_response.status_code == 200
    assert "contact" not in assign_response.json()

    return_response = await client.post(
        f"/organizations/{_ORG_SLUG}/opportunities/{opportunity_id}/return-to-ai"
    )
    assert return_response.status_code == 200
    assert "contact" not in return_response.json()

    await client.post(
        f"/organizations/{_ORG_SLUG}/opportunities/{opportunity_id}/assign-advisor",
        json={"advisor_id": advisor_id},
    )
    message_response = await client.post(
        f"/organizations/{_ORG_SLUG}/opportunities/{opportunity_id}/messages",
        json={"advisor_id": advisor_id, "content": "Hola"},
    )
    assert message_response.status_code == 200
    assert "contact" not in message_response.json()
