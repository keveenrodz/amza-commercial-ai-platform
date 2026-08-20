from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class WhatsAppMessageKey(BaseModel):
    model_config = ConfigDict(extra="ignore")

    remoteJid: str
    id: str
    fromMe: bool


class WhatsAppMessageContent(BaseModel):
    model_config = ConfigDict(extra="ignore")

    conversation: str | None = None  # texto plano, cuando content_type es texto


class WhatsAppMessageData(BaseModel):
    model_config = ConfigDict(extra="ignore")

    key: WhatsAppMessageKey
    message: WhatsAppMessageContent
    pushName: str | None = None
    messageTimestamp: int


class WhatsAppWebhookEvent(BaseModel):
    model_config = ConfigDict(extra="ignore")

    event: str
    data: WhatsAppMessageData
