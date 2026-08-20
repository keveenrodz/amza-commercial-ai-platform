"""
Bootstrap de InternalUser (Advisor o Administrator) -- sin contraseña que gestionar, la
autenticación es vía Google OAuth (spec 008). Llama al mismo caso de uso que usa la pantalla de
administración (spec 014) -- evita que la lógica de is_primary viva en dos lugares que puedan
desincronizarse. Sigue siendo el único camino para crear el primer usuario de una organización
nueva, antes de que exista ningún administrador que pueda usar la pantalla.

Uso:
    cd backend && python scripts/create_user.py --org amza-empaques --email juan@gmail.com \
        --name "Juan Perez" --role advisor
"""

from __future__ import annotations

import argparse
import asyncio

from app.use_cases.create_internal_user import CreateInternalUserUseCase
from core.enums.user import InternalUserRole
from core.exceptions.domain import DomainError
from infrastructure.database.session import AsyncSessionFactory


async def create_user(org_slug: str, email: str, full_name: str, role: str) -> None:
    use_case = CreateInternalUserUseCase(session_factory=AsyncSessionFactory)
    try:
        user = await use_case.execute(org_slug, full_name, email, InternalUserRole(role))
    except DomainError as exc:
        raise SystemExit(str(exc)) from exc

    primary_note = " [principal]" if user.is_primary else ""
    print(f"InternalUser creado: {user.full_name} <{user.email}> ({user.role.value}){primary_note}")


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
