from __future__ import annotations

from fastapi import Header, HTTPException

from app.config import settings


async def verify_telegram_secret(
    x_telegram_bot_api_secret_token: str = Header(default=""),
) -> None:
    if x_telegram_bot_api_secret_token != settings.telegram_webhook_secret:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")
