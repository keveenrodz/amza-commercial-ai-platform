# 007 API Layer

## Propósito

Exponer los casos de uso ya construidos (specs 005-006) vía HTTP: webhook de Telegram y
endpoints de gestión de oportunidades. Cablear `app/dependencies.py`, hoy vacío.

Este spec no introduce lógica de negocio nueva — con una única excepción puntual justificada en
la sección 3. Todo lo demás es orquestación: recibir petición, transformar a DTO interno, invocar
un caso de uso, devolver una respuesta.

---

## Principio: los routers solo orquestan

> Un router conoce únicamente: DTO de entrada → caso de uso → DTO de salida. Nunca repositorios,
> nunca providers (`AIProvider`, `ChannelProvider`), nunca entidades de dominio en la firma
> pública del endpoint.

Esto no es nuevo — ya estaba implícito en "los casos de uso nunca acceden directamente a la BD"
(`03_Engineering_Principles.md`) — pero es la primera vez que se pone a prueba en una capa HTTP,
así que se deja explícito. Dos consecuencias concretas de este principio en este spec:

- `Router → OpportunityRepository` directo: prohibido. Por eso existe `ListOpenOpportunitiesUseCase`
  (sección 4) aunque tenga cinco líneas — sin él, listar oportunidades forzaría al router a tocar
  el repositorio.
- `Router → TelegramChannelProvider` o `Router → OpenRouterAIProvider` directo: prohibido. El
  router del webhook llama a `ReceiveIncomingMessageUseCase`, que ya orquesta ambos providers
  internamente (spec 006). El router nunca los ve.

---

## Principio: un bot pertenece a una organización (no al revés)

Para el MVP, `Settings.telegram_bot_token` es un único token global y el mapeo bot → organización
se resuelve por **configuración operativa**, no por modelo de datos: quien registre el webhook en
Telegram (`setWebhook`) elige la URL, y esa URL incluye el `organization_slug` (sección 7). No
existe hoy una tabla que relacione bots con organizaciones — un bot apunta a una organización
porque así se configuró su webhook, nada más.

Esto deja la puerta abierta a **Organization → muchos bots** en el futuro sin romper el contrato
actual: el día que haga falta, `organization_slug` en la URL simplemente se resuelve contra una
tabla en vez de ser el único bot configurado, y el resto de este spec no cambia.

---

## 1. Bot API como único mecanismo de integración con Telegram

Confirmado con el usuario: se descarta MTProto/cliente (api_id + api_hash) para el MVP. Las
credenciales de `my.telegram.org` que existen en el repo corresponden a esa API distinta y no se
usan en este spec — la integración sigue siendo exclusivamente Bot API (REST + webhook), tal como
ya se implementó en `TelegramChannelProvider` (spec 006).

---

## 2. Corrección a Spec 006 — `app/config.py`

Nuevo setting para validar que las llamadas al webhook realmente vienen de Telegram:

```python
telegram_webhook_secret: str = ""
```

Se usa como `secret_token` al registrar el webhook con `setWebhook` (paso operativo manual, fuera
de este spec — un `curl` una vez por despliegue, no requiere código). Telegram lo reenvía en cada
llamada como header `X-Telegram-Bot-Api-Secret-Token`; si no coincide, se rechaza.

`.env.example` gana `TELEGRAM_WEBHOOK_SECRET=`.

---

## 3. Nuevo — `app/use_cases/list_open_opportunities.py`

Única pieza de lógica nueva de este spec. Sin él, el router de listado no tendría forma de llamar
al repositorio sin violar el principio de la sección anterior.

```python
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.entities.opportunity import Opportunity
from core.exceptions.domain import OrganizationSlugNotFoundError
from infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork


class ListOpenOpportunitiesUseCase:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def execute(self, organization_slug: str) -> list[Opportunity]:
        async with SQLAlchemyUnitOfWork(self._session_factory) as uow:
            organization = await uow.organizations.get_by_slug(organization_slug)
            if organization is None:
                raise OrganizationSlugNotFoundError(organization_slug)
            return await uow.opportunities.list_open_by_organization(organization.id)
```

---

## 4. Nuevo — `app/security.py`

Reemplaza el placeholder vacío. Dependencia de FastAPI que valida el secreto del webhook:

```python
from __future__ import annotations

from fastapi import Header, HTTPException

from app.config import settings


async def verify_telegram_secret(
    x_telegram_bot_api_secret_token: str = Header(default=""),
) -> None:
    if x_telegram_bot_api_secret_token != settings.telegram_webhook_secret:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")
```

Nota: este 401 es la única excepción a "el webhook nunca devuelve 4xx" (sección 8) — un secreto
inválido significa que la llamada no viene de Telegram, así que no hay reintento legítimo que
proteger. El 200-siempre aplica a llamadas ya autenticadas.

---

## 5. Nuevo — DTOs de la capa HTTP

Tres capas separadas, nunca se reutiliza una para otra: **FastAPI Request/Response → Input del
caso de uso → Entidad de dominio**. Ni siquiera cuando los campos coinciden hoy — proteger la
evolución futura de la API pública frente a cambios internos del dominio.

### `app/api/dto/telegram.py`

Modela solo lo que el MVP necesita del `Update` de Telegram. `extra="ignore"` porque Telegram
envía muchos más campos que no nos interesan.

```python
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class TelegramUser(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    first_name: str
    username: str | None = None


class TelegramChat(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int


class TelegramMessage(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    message_id: int
    from_user: TelegramUser = Field(alias="from")
    chat: TelegramChat
    text: str | None = None


class TelegramUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    update_id: int
    message: TelegramMessage | None = None
```

### `app/api/dto/opportunity.py`

```python
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.use_cases.get_conversation_history import ConversationHistory
from core.entities.message import Message
from core.entities.opportunity import Opportunity


class AssignAdvisorRequest(BaseModel):
    advisor_id: str


class OpportunityResponse(BaseModel):
    id: str
    contact_id: str
    agent_id: str
    attention_mode: str
    status: str
    channel_type: str
    started_at: datetime
    last_activity_at: datetime
    closed_at: datetime | None

    @classmethod
    def from_domain(cls, opportunity: Opportunity) -> OpportunityResponse:
        return cls(
            id=str(opportunity.id),
            contact_id=str(opportunity.contact_id),
            agent_id=str(opportunity.agent_id),
            attention_mode=opportunity.attention_mode.value,
            status=opportunity.status.value,
            channel_type=opportunity.channel_type.value,
            started_at=opportunity.started_at,
            last_activity_at=opportunity.last_activity_at,
            closed_at=opportunity.closed_at,
        )


class MessageResponse(BaseModel):
    id: str
    sender_role: str
    content: str
    content_type: str
    sent_at: datetime

    @classmethod
    def from_domain(cls, message: Message) -> MessageResponse:
        return cls(
            id=str(message.id),
            sender_role=message.sender_role.value,
            content=message.content,
            content_type=message.content_type.value,
            sent_at=message.sent_at,
        )


class ConversationHistoryResponse(BaseModel):
    opportunity: OpportunityResponse
    messages: list[MessageResponse]

    @classmethod
    def from_domain(cls, history: ConversationHistory) -> ConversationHistoryResponse:
        return cls(
            opportunity=OpportunityResponse.from_domain(history.opportunity),
            messages=[MessageResponse.from_domain(m) for m in history.messages],
        )
```

---

## 6. Nuevo — router del webhook

`app/api/routers/telegram_webhook.py`. Recibe el body como `dict[str, Any]`, nunca como
`TelegramUpdate` tipado directo en la firma — si se tipara directo, un `Update` que no calce con
el modelo (Telegram agrega campos con el tiempo) haría que FastAPI devuelva 422 automáticamente,
justo lo que la sección 8 prohíbe. Parsear a mano dentro del handler permite controlar el 100% de
las respuestas.

```python
from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, Depends, Response
from pydantic import ValidationError

from app.api.dto.telegram import TelegramUpdate
from app.dependencies import get_receive_incoming_message_use_case
from app.security import verify_telegram_secret
from app.use_cases.receive_incoming_message import (
    IncomingMessageInput,
    ReceiveIncomingMessageUseCase,
)
from core.enums.channel import ChannelType
from core.enums.message import MessageContentType

router = APIRouter(prefix="/webhooks/telegram", tags=["telegram"])
logger = structlog.get_logger()


@router.post("/{organization_slug}", dependencies=[Depends(verify_telegram_secret)])
async def receive_telegram_update(
    organization_slug: str,
    payload: dict[str, Any],
    use_case: ReceiveIncomingMessageUseCase = Depends(get_receive_incoming_message_use_case),
) -> Response:
    try:
        update = TelegramUpdate.model_validate(payload)
    except ValidationError:
        logger.warning("telegram.webhook.malformed_payload", organization_slug=organization_slug)
        return Response(status_code=200)

    if update.message is None:
        # edited_message, callback_query, channel_post, etc. — no soportado en el MVP. Se ignora
        # en silencio, nunca se rechaza (ver sección 8).
        return Response(status_code=200)

    message = update.message
    if message.text is None:
        # foto, sticker, ubicación sin texto — no soportado en el MVP, mismo criterio de arriba.
        # (Nota: chequear message.text directo, no update.message.text, para que mypy pueda
        # estrechar el tipo str | None a str en las líneas siguientes.)
        return Response(status_code=200)

    try:
        await use_case.execute(
            IncomingMessageInput(
                organization_slug=organization_slug,
                channel_type=ChannelType.TELEGRAM,
                external_contact_id=str(message.chat.id),
                contact_display_name=message.from_user.first_name,
                content=message.text,
                content_type=MessageContentType.TEXT,
                provider_message_id=str(message.message_id),
            )
        )
    except Exception:
        # Deliberadamente amplio, y solo aquí (contrastar con la sección 7: el router de
        # oportunidades NUNCA hace esto — un DomainError debe llegar al handler global como
        # 404/422/400, y un bug de programación debe volverse 500 visible de inmediato).
        #
        # No es que un reintento nunca ayudaría — un timeout o un rate limit del AIProvider sí
        # podrían resolverse reintentando. El punto es otro: no delegamos esa responsabilidad a
        # Telegram. Sus reintentos son ciegos (no sabe si ya procesamos el mensaje) y pueden
        # producir respuestas duplicadas al cliente o resúmenes generados dos veces — el costo de
        # ese reintento ciego es mayor que el beneficio. La estrategia del MVP es: una vez
        # validado el secreto, el webhook se considera recibido; cualquier fallo posterior se
        # registra para diagnóstico, no se convierte en una señal de "reintenta esto".
        # logger.exception() conserva el traceback completo, así que un bug de programación sigue
        # siendo visible en logs durante desarrollo — solo deja de propagarse como HTTP 5xx.
        #
        # Mejora futura anotada, no bloqueante: si aparece una jerarquía ProviderError explícita
        # (hoy no existe — OpenRouterAIProvider/TelegramChannelProvider dejan subir httpx.HTTPError
        # tal cual), separar el logging de "fallo de negocio" vs "fallo de infraestructura" para
        # mejor observabilidad. No cambia el resultado (200 en ambos casos), solo el detalle del log.
        logger.exception(
            "telegram.webhook.processing_failed",
            organization_slug=organization_slug,
        )

    return Response(status_code=200)
```

---

## 7. Nuevo — router de gestión de oportunidades

`app/api/routers/opportunities.py`. Rutas anidadas bajo `/organizations/{organization_slug}/...`
en vez de query params — la organización es parte del recurso, no un filtro opcional.

```python
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dto.opportunity import (
    AssignAdvisorRequest,
    ConversationHistoryResponse,
    OpportunityResponse,
)
from app.dependencies import (
    get_assign_to_advisor_use_case,
    get_get_conversation_history_use_case,
    get_list_open_opportunities_use_case,
    get_return_to_ai_use_case,
)
from app.use_cases.assign_to_advisor import AssignToAdvisorUseCase
from app.use_cases.get_conversation_history import GetConversationHistoryUseCase
from app.use_cases.list_open_opportunities import ListOpenOpportunitiesUseCase
from app.use_cases.return_to_ai import ReturnToAIUseCase
from core.value_objects.identifiers import InternalUserId, OpportunityId

router = APIRouter(prefix="/organizations/{organization_slug}/opportunities", tags=["opportunities"])


@router.get("")
async def list_open_opportunities(
    organization_slug: str,
    use_case: ListOpenOpportunitiesUseCase = Depends(get_list_open_opportunities_use_case),
) -> list[OpportunityResponse]:
    opportunities = await use_case.execute(organization_slug)
    return [OpportunityResponse.from_domain(o) for o in opportunities]


@router.get("/{opportunity_id}/history")
async def get_conversation_history(
    organization_slug: str,  # ignorado intencionalmente, ver nota de alcance abajo
    opportunity_id: str,
    use_case: GetConversationHistoryUseCase = Depends(get_get_conversation_history_use_case),
) -> ConversationHistoryResponse:
    history = await use_case.execute(OpportunityId.from_string(opportunity_id))
    return ConversationHistoryResponse.from_domain(history)


@router.post("/{opportunity_id}/assign-advisor")
async def assign_to_advisor(
    organization_slug: str,  # ignorado intencionalmente, ver nota de alcance abajo
    opportunity_id: str,
    body: AssignAdvisorRequest,
    use_case: AssignToAdvisorUseCase = Depends(get_assign_to_advisor_use_case),
) -> OpportunityResponse:
    opportunity = await use_case.execute(
        OpportunityId.from_string(opportunity_id),
        InternalUserId.from_string(body.advisor_id),
    )
    return OpportunityResponse.from_domain(opportunity)


@router.post("/{opportunity_id}/return-to-ai")
async def return_to_ai(
    organization_slug: str,  # ignorado intencionalmente, ver nota de alcance abajo
    opportunity_id: str,
    use_case: ReturnToAIUseCase = Depends(get_return_to_ai_use_case),
) -> OpportunityResponse:
    opportunity = await use_case.execute(OpportunityId.from_string(opportunity_id))
    return OpportunityResponse.from_domain(opportunity)
```

Nota de alcance (MVP): las rutas de un solo recurso (`/{opportunity_id}/...`) no validan que la
`opportunity` realmente pertenezca a `organization_slug` — `opportunity_id` es un UUID global y
ya es suficiente identificador. `organization_slug` se mantiene en la URL por consistencia de
diseño REST, no porque se use para autorizar. Se revisita si en algún momento se necesita
aislamiento multi-tenant estricto a nivel de URL (spec futuro, no antes).

---

## 8. Reglas del webhook (resumen ejecutable)

- Body inválido o no parseable → **200**, log de warning.
- `update.message` ausente (`edited_message`, `callback_query`, `channel_post`, etc.) → **200**,
  sin log — es tráfico esperado, no un error.
- `update.message.text` ausente (foto, sticker, ubicación — no soportado en MVP) → **200**, sin
  log.
- Fallo durante el procesamiento del caso de uso (organización inexistente, sin agente activo,
  error del `AIProvider`) → **200**, log de error (`logger.exception`).
- Secreto del webhook inválido (header no coincide) → **401** — única excepción; no es tráfico
  de Telegram real, no hay reintento que proteger.

Nunca 404, nunca 422 para una llamada con secreto válido — Telegram reintenta agresivamente ante
cualquier respuesta que no sea 2xx, y todas las causas de fallo de arriba son deterministas
(reintentar no las resuelve).

**Decisión de negocio, no técnica:** si `AIProvider`/`ChannelProvider` fallan (ej. OpenRouter caído
una hora), el mensaje del cliente se pierde — no hay reintento ni cola de reprocesamiento en el
MVP (Celery/Redis están fuera de alcance, ver `000_Technology_Stack.md`). La plataforma privilegia
evitar procesamiento duplicado (una respuesta repetida al cliente, un resumen generado dos veces)
sobre garantizar la entrega ante fallos de infraestructura. Es una decisión aceptada para el MVP,
no un descuido — se revisita si el volumen real de fallos lo justifica (ver spec 006, "Background
Jobs" en Future Evolution).

---

## 9. Corrección a Spec 006 — `app/dependencies.py`

Reemplaza el placeholder vacío. Lazy en vez de construcción eager al importar: cada `get_*` se
memoiza con `functools.lru_cache` (idiomático en FastAPI para dependencias singleton) — el primer
`Depends()` que la invoca la construye, los siguientes reciben la misma instancia. Importar este
módulo no construye nada por sí solo, evita efectos secundarios de red/config si algo lo importa
transitoriamente (tooling, tests, mypy). También expone `get_ai_provider`/`get_channel_provider`
directamente, no solo envueltos en use cases — los necesita el health check (sección 11).

```python
from __future__ import annotations

from functools import lru_cache

from app.config import settings
from app.services.conversation_context_assembler import ConversationContextAssembler
from app.services.conversation_summarization_service import ConversationSummarizationService
from app.use_cases.assign_to_advisor import AssignToAdvisorUseCase
from app.use_cases.get_conversation_history import GetConversationHistoryUseCase
from app.use_cases.list_open_opportunities import ListOpenOpportunitiesUseCase
from app.use_cases.receive_incoming_message import ReceiveIncomingMessageUseCase
from app.use_cases.return_to_ai import ReturnToAIUseCase
from core.interfaces.providers import AIProvider, ChannelProvider
from infrastructure.ai.openrouter import OpenRouterAIProvider
from infrastructure.channels.telegram import TelegramChannelProvider
from infrastructure.database.session import AsyncSessionFactory


@lru_cache
def get_ai_provider() -> AIProvider:
    return OpenRouterAIProvider(
        session_factory=AsyncSessionFactory,
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
    )


@lru_cache
def get_channel_provider() -> ChannelProvider:
    return TelegramChannelProvider(
        bot_token=settings.telegram_bot_token,
    )


@lru_cache
def get_context_assembler() -> ConversationContextAssembler:
    return ConversationContextAssembler(working_memory_size=settings.working_memory_size)


@lru_cache
def get_summarization_service() -> ConversationSummarizationService:
    return ConversationSummarizationService(
        ai_provider=get_ai_provider(),
        summarization_model=settings.summarization_model,
    )


@lru_cache
def get_receive_incoming_message_use_case() -> ReceiveIncomingMessageUseCase:
    return ReceiveIncomingMessageUseCase(
        session_factory=AsyncSessionFactory,
        ai_provider=get_ai_provider(),
        channel_provider=get_channel_provider(),
        context_assembler=get_context_assembler(),
        summarization_service=get_summarization_service(),
        summary_trigger_messages=settings.summary_trigger_messages,
    )


@lru_cache
def get_assign_to_advisor_use_case() -> AssignToAdvisorUseCase:
    return AssignToAdvisorUseCase(
        session_factory=AsyncSessionFactory,
        summarization_service=get_summarization_service(),
    )


@lru_cache
def get_return_to_ai_use_case() -> ReturnToAIUseCase:
    return ReturnToAIUseCase(
        session_factory=AsyncSessionFactory,
        summarization_service=get_summarization_service(),
    )


@lru_cache
def get_get_conversation_history_use_case() -> GetConversationHistoryUseCase:
    return GetConversationHistoryUseCase(session_factory=AsyncSessionFactory)


@lru_cache
def get_list_open_opportunities_use_case() -> ListOpenOpportunitiesUseCase:
    return ListOpenOpportunitiesUseCase(session_factory=AsyncSessionFactory)
```

`get_summarization_service()` llama `get_ai_provider()` en vez de recibirlo como parámetro —
`lru_cache` garantiza que ambos resuelven a la misma instancia cacheada, así que no hay
duplicación real, solo una llamada a función memoizada.

---

## 10. Nuevo — health endpoints

`AIProvider.health()`/`ChannelProvider.health()` existen desde spec 006 y no los usa nadie
todavía. `app/api/routers/health.py`:

```python
from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.dependencies import get_ai_provider, get_channel_provider
from core.interfaces.providers import AIProvider, ChannelProvider
from infrastructure.database.session import AsyncSessionFactory

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
async def readiness(
    ai_provider: AIProvider = Depends(get_ai_provider),
    channel_provider: ChannelProvider = Depends(get_channel_provider),
) -> JSONResponse:
    checks: dict[str, bool] = {}

    try:
        async with AsyncSessionFactory() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception:
        checks["database"] = False

    checks["openrouter"] = await ai_provider.health()
    checks["telegram"] = await channel_provider.health()

    status_code = 200 if all(checks.values()) else 503
    return JSONResponse(status_code=status_code, content=checks)
```

`/health` — liveness simple, el proceso está corriendo. `/health/ready` — verifica las tres
dependencias externas reales (DB, OpenRouter, Telegram) y agrega el detalle por dependencia en el
body, para que un fallo se diagnostique sin tener que revisar logs primero. No es para
Kubernetes (el MVP no lo usa) — es para soporte: un `curl` responde en segundos si el problema es
"OpenRouter caído" vs "el bot token venció" vs "la base de datos no responde".

---

## 11. Corrección a Spec 001 — `app/main.py`

Registrar los tres routers:

```python
from app.api.routers.health import router as health_router
from app.api.routers.opportunities import router as opportunities_router
from app.api.routers.telegram_webhook import router as telegram_webhook_router

# dentro de create_application(), antes del return:
application.include_router(health_router)
application.include_router(telegram_webhook_router)
application.include_router(opportunities_router)
```

---

## Próximo paso

Con 007, la plataforma queda operable de punta a punta: Telegram → webhook → use cases →
OpenRouter/Telegram providers → respuesta al cliente, más endpoints de gestión para que un
asesor humano tome/devuelva oportunidades. El roadmap de evoluciones futuras permanece el
registrado en spec 006 ("Future Evolution") — nada de esta spec lo modifica.
