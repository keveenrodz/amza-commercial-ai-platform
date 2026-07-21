"""
Cubre spec 010 (Advisor Reply):

1. Asesor asignado envía mensaje -> 200, persistido con sender_role="advisor",
   ChannelProvider.send() invocado.
2. Oportunidad todavía en modo AI (nadie la tomó) -> 422.
3. Oportunidad asignada a otro asesor -> 422 (mismo chequeo: assigned_advisor_id != advisor_id).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from httpx import AsyncClient

from app.dependencies import get_send_advisor_reply_use_case
from app.use_cases.send_advisor_reply import SendAdvisorReplyUseCase
from core.entities.contact import Contact
from core.entities.message import Message
from infrastructure.database.session import AsyncSessionFactory
from modules.agents.models.agent import AgentModel
from modules.configuration.models.organization import OrganizationModel
from modules.opportunities.models.contact import ContactModel
from modules.opportunities.models.conversation import ConversationModel
from modules.opportunities.models.opportunity import OpportunityModel
from scripts.create_user import create_user
from tests.test_security_and_identity import _ORG_SLUG, _login, _seed_organization


class _SpyChannelProvider:
    def __init__(self) -> None:
        self.sent: list[tuple[Message, Contact]] = []

    async def send(self, message: Message, contact: Contact) -> None:
        self.sent.append((message, contact))

    async def health(self) -> bool:
        return True


def _override_channel_provider(app, spy: _SpyChannelProvider) -> None:  # noqa: ANN001
    app.dependency_overrides[get_send_advisor_reply_use_case] = lambda: SendAdvisorReplyUseCase(
        session_factory=AsyncSessionFactory,
        channel_provider=spy,
    )


async def _seed_opportunity(
    *,
    organization_slug: str,
    attention_mode: str,
    assigned_advisor_id: uuid.UUID | None,
) -> uuid.UUID:
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
                external_id="12345",
                channel_type="telegram",
                display_name="Test Contact",
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
                status="waiting_for_advisor" if attention_mode == "human" else "qualified",
                attention_mode=attention_mode,
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
        return opportunity_id


async def test_assigned_advisor_can_send_message(client: AsyncClient) -> None:
    from app.main import app

    await _seed_organization()
    await create_user(_ORG_SLUG, "juan@gmail.com", "Juan Perez", "advisor")
    await _login(client, "juan@gmail.com")

    advisor_id = (await client.get("/auth/me")).json()["id"]

    opportunity_id = await _seed_opportunity(
        organization_slug=_ORG_SLUG,
        attention_mode="human",
        assigned_advisor_id=uuid.UUID(advisor_id),
    )

    spy = _SpyChannelProvider()
    _override_channel_provider(app, spy)

    response = await client.post(
        f"/organizations/{_ORG_SLUG}/opportunities/{opportunity_id}/messages",
        json={"advisor_id": advisor_id, "content": "Hola, ¿en qué te puedo ayudar?"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["sender_role"] == "advisor"
    assert body["content"] == "Hola, ¿en qué te puedo ayudar?"
    assert len(spy.sent) == 1


async def test_cannot_send_while_in_ai_mode(client: AsyncClient) -> None:
    await _seed_organization()
    await create_user(_ORG_SLUG, "juan@gmail.com", "Juan Perez", "advisor")
    await _login(client, "juan@gmail.com")

    advisor_id = (await client.get("/auth/me")).json()["id"]

    opportunity_id = await _seed_opportunity(
        organization_slug=_ORG_SLUG,
        attention_mode="ai",
        assigned_advisor_id=None,
    )

    response = await client.post(
        f"/organizations/{_ORG_SLUG}/opportunities/{opportunity_id}/messages",
        json={"advisor_id": advisor_id, "content": "Hola"},
    )

    assert response.status_code == 422


async def test_cannot_send_when_assigned_to_another_advisor(client: AsyncClient) -> None:
    await _seed_organization()
    await create_user(_ORG_SLUG, "juan@gmail.com", "Juan Perez", "advisor")
    await _login(client, "juan@gmail.com")

    advisor_id = (await client.get("/auth/me")).json()["id"]

    opportunity_id = await _seed_opportunity(
        organization_slug=_ORG_SLUG,
        attention_mode="human",
        assigned_advisor_id=uuid.uuid4(),
    )

    response = await client.post(
        f"/organizations/{_ORG_SLUG}/opportunities/{opportunity_id}/messages",
        json={"advisor_id": advisor_id, "content": "Hola"},
    )

    assert response.status_code == 422
