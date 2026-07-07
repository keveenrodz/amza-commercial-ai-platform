"""
Bootstrap de InternalUser (Advisor o Administrator) -- sin contraseña que gestionar, la
autenticación es vía Google OAuth (spec 008). No hay distinción técnica entre roles a nivel de
comando: create_user sirve para ambos, el rol es solo un valor.

Uso:
    cd backend && python scripts/create_user.py --org amza-empaques --email juan@gmail.com \
        --name "Juan Perez" --role advisor
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import UTC, datetime

from core.entities.internal_user import InternalUser
from core.enums.user import InternalUserRole, InternalUserStatus
from core.value_objects.identifiers import InternalUserId
from infrastructure.database.session import AsyncSessionFactory
from infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork


async def create_user(org_slug: str, email: str, full_name: str, role: str) -> None:
    async with SQLAlchemyUnitOfWork(AsyncSessionFactory) as uow:
        organization = await uow.organizations.get_by_slug(org_slug)
        if organization is None:
            raise SystemExit(f"No existe ninguna Organization con slug {org_slug!r}")

        existing = await uow.internal_users.get_by_email(email)
        if existing is not None:
            raise SystemExit(f"Ya existe un InternalUser con email {email!r} ({existing.id})")

        now = datetime.now(tz=UTC)
        user = InternalUser(
            id=InternalUserId.generate(),
            organization_id=organization.id,
            full_name=full_name,
            email=email,
            role=InternalUserRole(role),
            status=InternalUserStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        await uow.internal_users.save(user)
        await uow.commit()

    print(f"InternalUser creado: {full_name} <{email}> ({role}) en {org_slug}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Crea un InternalUser (Advisor o Administrator) -- sin contraseña"
    )
    parser.add_argument("--org", required=True, help="slug de la Organization")
    parser.add_argument(
        "--email", required=True, help="email de Google con el que la persona iniciará sesión"
    )
    parser.add_argument("--name", required=True, dest="full_name")
    parser.add_argument("--role", required=True, choices=["advisor", "administrator"])
    args = parser.parse_args()
    asyncio.run(create_user(args.org, args.email, args.full_name, args.role))


if __name__ == "__main__":
    main()
