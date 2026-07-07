from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol


@dataclass(frozen=True)
class AuthenticatedIdentity:
    email: str
    full_name: str
    provider: Literal["google"]


class AuthProvider(Protocol):
    def get_authorization_url(self, state: str, redirect_uri: str) -> str: ...

    async def exchange_code(self, code: str, redirect_uri: str) -> AuthenticatedIdentity: ...
