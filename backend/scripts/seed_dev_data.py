"""
Seed de datos de desarrollo para probar el flujo completo Telegram -> AI -> Telegram.

Crea una Organization + Agent si no existen (idempotente, se puede correr varias veces).
No usa OrganizationRepository porque a propósito no expone save() -- crear organizaciones
no es una operación que la aplicación haga en tiempo de ejecución, solo una tarea de
aprovisionamiento/ops. Este script es exactamente eso: ops, no código de producto.

Uso:
    cd backend && python scripts/seed_dev_data.py
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime

from sqlalchemy import select

from infrastructure.database.session import AsyncSessionFactory
from modules.agents.models.agent import AgentModel
from modules.configuration.models.organization import OrganizationModel

ORGANIZATION_SLUG = "amza-empaques"

_SYSTEM_PROMPT = (
    "Eres el asistente comercial de Amza Empaques, una empresa que vende empaques compostables "
    "y biodegradables principalmente en material de bagazo de caña de azúcar. Responde de "
    "forma breve, cordial y profesional en español. Tu objetivo es entender qué necesita el "
    "cliente (tipo de empaque, cantidad, uso) para poder ayudarlo. Si no tienes la información "
    "para cotizar, pide los datos que falten."
)

_AGENT_MODEL = "openai/gpt-4.1-nano" #"deepseek/deepseek-v4-flash"


async def seed() -> None:
    async with AsyncSessionFactory() as session:
        result = await session.execute(
            select(OrganizationModel).where(OrganizationModel.slug == ORGANIZATION_SLUG)
        )
        organization = result.scalar_one_or_none()
        if organization is None:
            now = datetime.now(tz=UTC)
            organization = OrganizationModel(
                id=uuid.uuid4(),
                name="Amza Empaques",
                slug=ORGANIZATION_SLUG,
                timezone="America/Bogota",
                language="es",
                status="active",
                created_at=now,
                updated_at=now,
            )
            session.add(organization)
            await session.flush()
            print(f"Organization creada: {organization.slug} ({organization.id})")
        else:
            print(f"Organization ya existe: {organization.slug} ({organization.id})")

        result = await session.execute(
            select(AgentModel).where(AgentModel.organization_id == organization.id)
        )
        agent = result.scalars().first()
        if agent is None:
            now = datetime.now(tz=UTC)
            agent = AgentModel(
                id=uuid.uuid4(),
                organization_id=organization.id,
                name="Asistente Comercial Amza",
                system_prompt=_SYSTEM_PROMPT,
                model=_AGENT_MODEL,
                status="active",
                created_at=now,
                updated_at=now,
            )
            session.add(agent)
            print(f"Agent creado: {agent.name} ({agent.id}), modelo={agent.model}")
        else:
            print(f"Agent ya existe: {agent.name} ({agent.id}), modelo={agent.model}")

        await session.commit()

    print(f"\nListo. organization_slug para el webhook: {ORGANIZATION_SLUG}")


if __name__ == "__main__":
    asyncio.run(seed())
