"""
Registra el webhook de Telegram apuntando a una URL pública (ngrok en desarrollo local).

Herramienta de desarrollo, no código de producto -- en producción el webhook se registra una
sola vez y no necesita este script (ver spec 007). Aquí sí vale la pena porque la URL de ngrok
cambia cada reinicio en el plan free, así que este comando se corre varias veces por sesión de
trabajo. Toma el token del bot y el secreto del webhook de Settings -- nunca hay que copiarlos
a mano.

Uso:
    cd backend && python scripts/register_telegram_webhook.py https://tu-url.ngrok-free.dev
"""

from __future__ import annotations

import asyncio
import sys

import httpx

from app.config import settings

# Debe coincidir con ORGANIZATION_SLUG en seed_dev_data.py -- no se importa desde ahí porque
# scripts/ no está registrado como paquete instalable (a propósito, no es una librería del
# proyecto), así que "from scripts.X import Y" no resuelve sin importar el cwd.
ORGANIZATION_SLUG = "amza-empaques"


async def register(public_url: str) -> None:
    webhook_url = f"{public_url.rstrip('/')}/webhooks/telegram/{ORGANIZATION_SLUG}"

    async with httpx.AsyncClient(
        base_url=f"https://api.telegram.org/bot{settings.telegram_bot_token}"
    ) as client:
        result = await client.post(
            "/setWebhook",
            json={
                "url": webhook_url,
                "secret_token": settings.telegram_webhook_secret,
                "allowed_updates": ["message"],
            },
        )
        print("setWebhook:", result.json())

        info = await client.get("/getWebhookInfo")
        print("getWebhookInfo:", info.json())


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python scripts/register_telegram_webhook.py <url-publica>")
        sys.exit(1)
    asyncio.run(register(sys.argv[1]))
