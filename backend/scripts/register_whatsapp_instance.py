"""
Crea la instancia de WhatsApp en Evolution API y registra el webhook en la misma llamada, e
imprime el código QR (base64) para escanear con el WhatsApp de +57 301 509 2386.

Herramienta de desarrollo/aprovisionamiento, no código de producto -- se corre una sola vez por
número, no es de uso diario (ver spec 016 sección 5). Toma la URL/API key de Evolution API y el
secreto del webhook de Settings -- nunca hay que copiarlos a mano.

Uso:
    cd backend && python scripts/register_whatsapp_instance.py https://tu-url-publica
"""

from __future__ import annotations

import asyncio
import base64
import sys
from pathlib import Path

import httpx

from app.config import settings

# Debe coincidir con ORGANIZATION_SLUG en seed_dev_data.py / register_telegram_webhook.py -- no
# se importa desde ahí, mismo motivo: scripts/ no es un paquete instalable.
ORGANIZATION_SLUG = "amza-empaques"


async def register_whatsapp_instance(webhook_base_url: str) -> None:
    webhook_url = f"{webhook_base_url.rstrip('/')}/webhooks/whatsapp/{ORGANIZATION_SLUG}"

    async with httpx.AsyncClient(
        base_url=settings.evolution_api_base_url,
        headers={"apikey": settings.evolution_api_key},
    ) as client:
        response = await client.post(
            "/instance/create",
            json={
                "instanceName": settings.evolution_instance_name,
                "qrcode": True,
                # Requerido en la práctica (no documentado con claridad al escribir spec 016):
                # sin esto, /instance/create devuelve 400 "Invalid integration". BAILEYS es el
                # protocolo de WhatsApp Web no oficial -- la otra opción real, WHATSAPP-BUSINESS,
                # es la API oficial de Meta (de pago, requiere aprobación de Meta), fuera de
                # alcance de este spec.
                "integration": "WHATSAPP-BAILEYS",
                "webhook": {
                    "enabled": True,
                    "url": webhook_url,
                    "events": ["MESSAGES_UPSERT"],
                    "headers": {"X-Webhook-Secret": settings.whatsapp_webhook_secret},
                },
            },
        )
        response.raise_for_status()
        data = response.json()

    print("Instancia creada:", data["instance"]["instanceName"])

    qr_base64 = data["qrcode"]["base64"]
    qr_path = Path(__file__).resolve().parent / "whatsapp_qr.png"
    # El base64 puede venir con el prefijo "data:image/png;base64,"; se limpia antes de decodificar.
    qr_base64 = qr_base64.removeprefix("data:image/png;base64,")
    qr_path.write_bytes(base64.b64decode(qr_base64))

    print(f"Código QR guardado en: {qr_path}")
    print("Escanea con el WhatsApp de +57 301 509 2386 (ábrelo en cualquier visor de imágenes).")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python scripts/register_whatsapp_instance.py <url-publica>")
        sys.exit(1)
    asyncio.run(register_whatsapp_instance(sys.argv[1]))
