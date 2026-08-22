from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from infrastructure.channels.whatsapp import WhatsAppConnectionInfo


class WhatsAppStatusResponse(BaseModel):
    connected: bool
    phone_number: str | None

    @classmethod
    def from_domain(cls, info: WhatsAppConnectionInfo) -> WhatsAppStatusResponse:
        return cls(connected=info.connected, phone_number=info.phone_number)


class WhatsAppMessageKey(BaseModel):
    model_config = ConfigDict(extra="ignore")

    remoteJid: str
    # WhatsApp está migrando a un identificador "LID" -- el mismo contacto real puede llegar
    # unas veces como remoteJid="<lid>@lid" y otras como "<numero>@s.whatsapp.net". Cuando llega
    # en formato LID, Evolution API manda además este campo con el JID de número real -- sin
    # normalizar contra él, el mismo cliente se registraba como dos Contact distintos según qué
    # formato trajera cada mensaje (visto en producción real: mismo número, dos conversaciones).
    remoteJidAlt: str | None = None
    id: str
    fromMe: bool

    @property
    def canonical_jid(self) -> str:
        """Prefiere siempre el JID de número real (@s.whatsapp.net) sobre el LID -- es el que
        identifica al cliente de forma estable independientemente de qué formato traiga un
        mensaje puntual."""
        if self.remoteJid.endswith("@lid") and self.remoteJidAlt is not None:
            return self.remoteJidAlt
        return self.remoteJid


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
