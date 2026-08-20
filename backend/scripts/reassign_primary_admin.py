"""
Mueve la insignia de administrador "principal" a otro Administrator de la misma organización --
caso raro y de alto riesgo (ej. la cuenta de Google del principal se perdió), deliberadamente sin
exponer como endpoint (ver spec 014, sección 6). Una sola transacción: quita is_primary al
anterior y lo pone en el nuevo, para que el índice único parcial de la migración 0005 nunca vea
dos principales a la vez.

Uso:
    cd backend && python scripts/reassign_primary_admin.py --org amza-empaques \
        --email nuevo-principal@gmail.com
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import UTC, datetime

from core.enums.user import InternalUserRole, InternalUserStatus
from infrastructure.database.session import AsyncSessionFactory
from infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork


async def reassign_primary_admin(org_slug: str, email: str) -> None:
    async with SQLAlchemyUnitOfWork(AsyncSessionFactory) as uow:
        organization = await uow.organizations.get_by_slug(org_slug)
        if organization is None:
            raise SystemExit(f"No existe ninguna Organization con slug {org_slug!r}")

        new_primary = await uow.internal_users.get_by_email(email)
        if new_primary is None:
            raise SystemExit(f"No existe ningún InternalUser con email {email!r}")
        if new_primary.organization_id != organization.id:
            raise SystemExit(f"{email!r} no pertenece a la organización {org_slug!r}")
        if new_primary.role != InternalUserRole.ADMINISTRATOR:
            raise SystemExit(f"{email!r} no es Administrator -- no puede ser principal")
        if new_primary.status != InternalUserStatus.ACTIVE:
            raise SystemExit(f"{email!r} está inactivo -- reactívalo antes de hacerlo principal")
        if new_primary.is_primary:
            raise SystemExit(f"{email!r} ya es el administrador principal")

        current_primary = await uow.internal_users.get_primary_administrator(organization.id)

        now = datetime.now(tz=UTC)
        if current_primary is not None:
            current_primary.is_primary = False
            current_primary.updated_at = now
            await uow.internal_users.save(current_primary)

        new_primary.is_primary = True
        new_primary.updated_at = now
        await uow.internal_users.save(new_primary)
        await uow.commit()

    previous = f" (antes: {current_primary.email})" if current_primary else ""
    print(f"Nuevo administrador principal de {org_slug!r}: {email}{previous}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reasigna el administrador principal de una organización"
    )
    parser.add_argument("--org", required=True, help="slug de la Organization")
    parser.add_argument("--email", required=True, help="email del nuevo administrador principal")
    args = parser.parse_args()
    asyncio.run(reassign_primary_admin(args.org, args.email))


if __name__ == "__main__":
    main()
