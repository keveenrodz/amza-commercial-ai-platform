# 006 Conversation Memory & Provider Implementations

## Propósito

Reemplazar la estrategia de contexto de spec 005 ("últimos 50 mensajes, resumir si hay 2h de
inactividad") por un diseño de memoria conversacional en capas, y entregar las primeras
implementaciones concretas de `AIProvider` (OpenRouter) y `ChannelProvider` (Telegram).

Nota de alcance: el plan original contemplaba providers + API layer en un solo spec. Ese alcance
se divide: **006 cubre memoria conversacional y providers**; la capa HTTP (routers FastAPI +
wiring de `app/dependencies.py`) pasa a **spec 007**, siguiendo el mismo patrón de capa-por-spec
usado desde 002.

---

## Principio arquitectónico

> Los servicios de aplicación deciden qué tarea de IA ejecutar. `AIProvider` únicamente ejecuta
> inferencias sobre un modelo. Nunca contiene lógica de negocio ni conocimiento sobre el
> propósito de la llamada.

Esto es lo que impide que `AIProvider` termine acumulando `summarize()`, `translate()`,
`classify()`, `extract_entities()`, etc. — un método por cada nueva tarea de IA que aparezca en
el negocio. El provider expone dos **capacidades técnicas** (conversar con un agente, completar
un prompt libre), no una lista creciente de **casos de uso**.

---

## 1. Corrección a Spec 002 — `core/interfaces/providers.py`

`generate()` deja de recibir `list[Message]` crudo — recibe un `ConversationContext` ya
ensamblado (resumen + mensajes recientes), para que el provider no mezcle resumen y mensajes
reales al construir el prompt. Se agrega `complete()` como primitiva de texto libre, sin atarse
a ningún `Agent`, para que la app pueda ejecutar tareas de IA (resúmenes, y en el futuro
clasificación, extracción, etc.) sin tocar esta interfaz cada vez.

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from core.entities.contact import Contact
from core.entities.message import Message
from core.value_objects.identifiers import AgentId


@dataclass(frozen=True)
class ConversationContext:
    summary: str | None
    recent_messages: list[Message]


@dataclass(frozen=True)
class CompletionRequest:
    model: str
    system_prompt: str
    user_prompt: str
    temperature: float = 0.0
    max_tokens: int | None = None
    timeout: float | None = None


class ChannelProvider(Protocol):
    async def send(self, message: Message, contact: Contact) -> None: ...

    async def health(self) -> bool: ...


class AIProvider(Protocol):
    async def generate(self, context: ConversationContext, agent_id: AgentId) -> str: ...

    async def complete(self, request: CompletionRequest) -> str: ...

    async def health(self) -> bool: ...
```

`response_format` (JSON mode) queda fuera de `CompletionRequest` deliberadamente — no hay hoy
ningún caso de uso que lo necesite, y su soporte varía por modelo en OpenRouter. Se agrega el día
que exista una tarea real que lo requiera (ver Future Evolution). `timeout` sí se incluye desde
ya, aunque hoy no se use explícitamente: es un parámetro de la llamada HTTP, no del negocio, y
va a aparecer tan pronto se implemente `OpenRouterAIProvider` — mejor tenerlo en el contrato desde
el inicio que agregarlo como cambio breaking después.

`ConversationContext.summary: str | None` — `None` significa exclusivamente "todavía no existe
un resumen para esta conversación". `ConversationSummarizationService` nunca persiste un resumen
vacío (ver guard en la sección 8), así que no existe el caso "existe pero está vacío" — no hace
falta un campo `has_summary` adicional.

**Corrección post end-to-end (encontrada probando con Telegram real, no en el diseño original):**
`ChannelProvider.send()` originalmente recibía `Message` + `Opportunity`, y el provider resolvía
`Contact` internamente vía `ContactRepository` a partir de `opportunity.contact_id` (mismo
criterio que `AIProvider.generate()` con `Agent`, ver sección 13). Eso rompía en el caso real más
común — un contacto nuevo escribiendo por primera vez — porque el `Contact` se crea en la misma
transacción del use case que todavía no ha hecho `commit()`, y el provider abre una **sesión
separada** para buscarlo: esa sesión no ve la fila sin confirmar, lanza `ContactNotFoundError`, y
la transacción completa hace rollback — se pierde todo, nunca llega respuesta, sin ningún error
visible más allá de un log. La firma cambió a `send(message: Message, contact: Contact)`: el use
case ya tiene el `Contact` en memoria, se lo pasa directo, el provider no vuelve a tocar la BD.
Esto resuelve — para este provider específicamente — el ADR pendiente de la sección "ADR
pendiente de evaluación durante implementación": la evidencia de que el acoplamiento a
repositorios complica el código en la práctica ya existe, no es hipotética.

---

## 2. Corrección a Spec 002 — nueva entidad `ConversationSummary`

Un resumen no es un `Message`. Guardarlo como `Message(sender_role=SYSTEM)` (como sugería el TODO
de spec 005) obligaría a filtrar `SYSTEM` en cada consulta de historial, conteo o export.
Se modela como entidad propia, versionada (append-only, nunca `UPDATE`) — un resumen generado
por LLM no es determinista, y perder la versión anterior imposibilita auditar por qué el agente
dijo algo incorrecto.

`backend/core/entities/conversation_summary.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from core.value_objects.identifiers import ConversationId, ConversationSummaryId


@dataclass
class ConversationSummary:
    id: ConversationSummaryId
    conversation_id: ConversationId
    summary: str
    up_to_sent_at: datetime
    version: int
    created_at: datetime
```

`up_to_sent_at` marca el `sent_at` del último mensaje incluido en este resumen — es el cursor
que permite calcular "mensajes nuevos desde el último resumen" sin depender de un contador
derivado en `Conversation` (que introduciría un campo a mantener consistente en cada insert de
`Message`, sin necesidad real a este volumen).

`version` es monótonamente creciente dentro de cada conversación y nunca se reinicia — ni al
cambiar de modelo de IA, ni al reasignar la conversación entre AI/asesor. Parece obvio, pero se
deja escrito para que no quede a interpretación de quien implemente el repositorio.

---

## 3. Corrección a Spec 002 — `core/value_objects/identifiers.py`

Agregar el ID tipado para la nueva entidad:

```python
@dataclass(frozen=True)
class ConversationSummaryId(_BaseId):
    pass
```

---

## 4. Corrección a Spec 002 — `core/interfaces/repositories.py`

`MessageRepository` gana dos métodos para soportar el cálculo de umbral y la obtención del
bloque a resumir. `ConversationSummaryRepository` es un Protocol nuevo. `UnitOfWork` expone
ambos.

```python
class MessageRepository(Protocol):
    async def get_by_id(self, id: MessageId) -> Message | None: ...

    async def list_by_conversation(
        self,
        conversation_id: ConversationId,
        limit: int,
    ) -> list[Message]: ...

    async def list_since(
        self,
        conversation_id: ConversationId,
        after: datetime | None,
    ) -> list[Message]: ...

    async def count_since(
        self,
        conversation_id: ConversationId,
        after: datetime | None,
    ) -> int: ...

    async def save(self, message: Message) -> None: ...


class ConversationSummaryRepository(Protocol):
    async def get_latest(
        self,
        conversation_id: ConversationId,
    ) -> ConversationSummary | None: ...

    async def save(self, summary: ConversationSummary) -> None: ...


class UnitOfWork(Protocol):
    opportunities: OpportunityRepository
    conversations: ConversationRepository
    messages: MessageRepository
    conversation_summaries: ConversationSummaryRepository
    contacts: ContactRepository
    agents: AgentRepository
    organizations: OrganizationRepository
    internal_users: InternalUserRepository

    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...
    async def __aenter__(self) -> UnitOfWork: ...
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None: ...
```

`after=None` significa "sin cota inferior" (conversación sin resumen previo — se cuenta/lista
desde el inicio). `after` es **exclusivo** en ambos métodos: `sent_at > after`, nunca `>=`. Si se
implementa con `>=`, el mensaje que cerró el resumen anterior (`up_to_sent_at`) se cuenta y se
resume dos veces.

---

## 5. Corrección a Spec 003 — Persistencia

Nueva tabla en `modules/memory/models/conversation_summary.py` (el módulo ya existe, vacío,
desde spec 001):

```python
from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.database.base import Base


class ConversationSummaryModel(Base):
    __tablename__ = "conversation_summaries"
    __table_args__ = (
        sa.Index(
            "ix_conversation_summaries_conversation_id_version",
            "conversation_id",
            "version",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid(native_uuid=False), primary_key=True)
    conversation_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid(native_uuid=False), nullable=False)
    summary: Mapped[str] = mapped_column(sa.Text, nullable=False)
    up_to_sent_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    version: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
```

Migración `0003_add_conversation_summaries.py`: crea la tabla de arriba, y agrega un índice
compuesto `(conversation_id, sent_at)` sobre `messages` — hoy tiene dos índices simples
(`conversation_id` y `sent_at` por separado); `list_since`/`count_since` filtran por ambas
columnas a la vez, así que un índice compuesto les sirve mejor que los dos simples.

---

## 6. Corrección a Spec 004 — Repositorios

`modules/memory/repositories/conversation_summary.py` (mismo patrón `_to_entity`/`_from_entity`
que el resto):

```python
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.entities.conversation_summary import ConversationSummary
from core.value_objects.identifiers import ConversationId, ConversationSummaryId
from modules.memory.models.conversation_summary import ConversationSummaryModel


def _to_entity(model: ConversationSummaryModel) -> ConversationSummary:
    return ConversationSummary(
        id=ConversationSummaryId(value=model.id),
        conversation_id=ConversationId(value=model.conversation_id),
        summary=model.summary,
        up_to_sent_at=model.up_to_sent_at,
        version=model.version,
        created_at=model.created_at,
    )


def _from_entity(entity: ConversationSummary) -> ConversationSummaryModel:
    return ConversationSummaryModel(
        id=entity.id.value,
        conversation_id=entity.conversation_id.value,
        summary=entity.summary,
        up_to_sent_at=entity.up_to_sent_at,
        version=entity.version,
        created_at=entity.created_at,
    )


class SQLAlchemyConversationSummaryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_latest(
        self,
        conversation_id: ConversationId,
    ) -> ConversationSummary | None:
        result = await self._session.execute(
            select(ConversationSummaryModel)
            .where(ConversationSummaryModel.conversation_id == conversation_id.value)
            .order_by(ConversationSummaryModel.version.desc())
            .limit(1)
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model else None

    async def save(self, summary: ConversationSummary) -> None:
        self._session.add(_from_entity(summary))
```

`save()` usa `add()`, no `merge()` — los summaries son append-only, nunca se actualiza uno
existente (a diferencia del resto de repositorios).

`SQLAlchemyMessageRepository` gana `list_since`/`count_since`:

```python
    async def list_since(
        self,
        conversation_id: ConversationId,
        after: datetime | None,
    ) -> list[Message]:
        # after es exclusivo: sent_at > after, nunca >= (evita re-resumir el mensaje de corte)
        stmt = select(MessageModel).where(MessageModel.conversation_id == conversation_id.value)
        if after is not None:
            stmt = stmt.where(MessageModel.sent_at > after)
        result = await self._session.execute(stmt.order_by(MessageModel.sent_at.asc()))
        return [_to_entity(m) for m in result.scalars().all()]

    async def count_since(
        self,
        conversation_id: ConversationId,
        after: datetime | None,
    ) -> int:
        stmt = select(func.count()).select_from(MessageModel).where(
            MessageModel.conversation_id == conversation_id.value
        )
        if after is not None:
            stmt = stmt.where(MessageModel.sent_at > after)
        result = await self._session.execute(stmt)
        return result.scalar_one()
```

`SQLAlchemyUnitOfWork` agrega `conversation_summaries` al `__aenter__`.

---

## 7. Nuevo — `app/services/conversation_context_assembler.py`

Responsabilidad única: dado un `conversation_id`, devolver el `ConversationContext` para
**responder** al cliente. Compone el último resumen (si existe) con la ventana de mensajes
recientes — nunca decide cuándo resumir, eso es responsabilidad del servicio de la sección 8.

```python
from __future__ import annotations

from core.interfaces.providers import ConversationContext
from core.interfaces.repositories import UnitOfWork
from core.value_objects.identifiers import ConversationId


class ConversationContextAssembler:
    def __init__(self, working_memory_size: int) -> None:
        self._working_memory_size = working_memory_size

    async def assemble(
        self,
        conversation_id: ConversationId,
        uow: UnitOfWork,
    ) -> ConversationContext:
        latest_summary = await uow.conversation_summaries.get_latest(conversation_id)
        recent_messages = await uow.messages.list_by_conversation(
            conversation_id,
            limit=self._working_memory_size,
        )
        return ConversationContext(
            summary=latest_summary.summary if latest_summary else None,
            recent_messages=recent_messages,
        )
```

---

## 8. Nuevo — `app/services/conversation_summarization_service.py`

> `ConversationSummarizationService` nunca decide **si** debe regenerarse un resumen — solo sabe
> **cómo** generar uno. Esa decisión pertenece siempre al caller (`ReceiveIncomingMessageUseCase`,
> `AssignToAdvisorUseCase`, `ReturnToAIUseCase`).

Se documenta explícitamente para evitar que, con el tiempo, alguien mueva un `if message_count >=
threshold` dentro del servicio "para simplificar" — eso acoplaría el servicio a una única
política de disparo y le impediría a otro caller pedir un resumen incondicional (como hacen
`AssignToAdvisorUseCase`/`ReturnToAIUseCase` en la sección 10). La separación de responsabilidad
es:

- **Use cases** → deciden cuándo.
- **`ConversationSummarizationService`** → sabe cómo.
- **`AIProvider`** → sabe cómo hablar con el LLM.

Habla directo con `MessageRepository` y `ConversationSummaryRepository` — no reutiliza
`ConversationContextAssembler`, porque necesita una ventana de datos distinta (todos los mensajes
desde el último resumen, no los últimos N).

```python
from __future__ import annotations

from datetime import UTC, datetime

from core.entities.conversation_summary import ConversationSummary
from core.interfaces.providers import AIProvider, CompletionRequest
from core.interfaces.repositories import UnitOfWork
from core.value_objects.identifiers import ConversationId, ConversationSummaryId

# Placeholder — no es un contrato definitivo. Este prompt cambiará varias veces antes de
# estabilizarse; cuando eso empiece a doler, ver spec 014 (Prompt Management) en Future Evolution.
_SUMMARY_SYSTEM_PROMPT = (
    "Resume la siguiente conversación comercial en 3-5 frases. Conserva intención de compra, "
    "necesidades, objeciones, acuerdos y cualquier dato que un asesor humano necesite para continuarla."
)


class ConversationSummarizationService:
    def __init__(self, ai_provider: AIProvider, summarization_model: str) -> None:
        self._ai_provider = ai_provider
        self._summarization_model = summarization_model

    async def execute(self, conversation_id: ConversationId, uow: UnitOfWork) -> None:
        previous = await uow.conversation_summaries.get_latest(conversation_id)
        since = previous.up_to_sent_at if previous else None

        new_messages = await uow.messages.list_since(conversation_id, after=since)
        if not new_messages:
            return

        transcript = "\n".join(f"{m.sender_role.value}: {m.content}" for m in new_messages)
        user_prompt = (
            f"Resumen anterior:\n{previous.summary}\n\n---\n\nNuevos mensajes:\n{transcript}"
            if previous
            else transcript
        )

        summary_text = await self._ai_provider.complete(
            CompletionRequest(
                model=self._summarization_model,
                system_prompt=_SUMMARY_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=0.0,
            )
        )

        await uow.conversation_summaries.save(
            ConversationSummary(
                id=ConversationSummaryId.generate(),
                conversation_id=conversation_id,
                summary=summary_text,
                up_to_sent_at=new_messages[-1].sent_at,
                version=(previous.version + 1) if previous else 1,
                created_at=datetime.now(tz=UTC),
            )
        )
```

El guard `if not new_messages: return` cubre el caso donde `AssignToAdvisorUseCase` y
`ReturnToAIUseCase` (sección 10) disparan el servicio sin que haya mensajes nuevos desde el
último resumen — evita una llamada a `complete()` sin nada que resumir.

---

## 9. Corrección a Spec 005 — `ReceiveIncomingMessageUseCase`

Cambios sobre `backend/app/use_cases/receive_incoming_message.py`:

- `_build_context()` se elimina; se reemplaza por `self._context_assembler.assemble(...)`.
- `_AI_CONTEXT_MESSAGES = 50` se elimina; el tamaño de ventana lo controla
  `settings.working_memory_size`, inyectado en `ConversationContextAssembler`.
- Después de `channel_provider.send()` y del `commit()` de la transacción principal, se abre una
  **segunda transacción** exclusivamente para evaluar y, si corresponde, generar el resumen.
  Separarla de la transacción principal logra dos cosas: no alarga la sesión/conexión que ya
  está sirviendo al cliente, y aísla el fallo — si `complete()` lanza (OpenRouter caído, rate
  limit), el mensaje que el cliente ya recibió por Telegram no se ve afectado.
- El bloque de resumen va en `try/except` explícito: un fallo se loguea como warning y no se
  propaga. Es best-effort — si el proceso muere antes de persistir el resumen, se pierde esa
  actualización y se recalculará en el siguiente disparo. No se usa `asyncio.create_task()`: sin
  cola de tareas ni supervisión, una excepción dentro de un task sin `await` se traga en
  silencio, lo que sería peor que el costo de la segunda llamada síncrona.

```python
            if opportunity.attention_mode == AttentionMode.AI:
                context = await self._context_assembler.assemble(conversation.id, uow)
                response_text = await self._ai_provider.generate(context, opportunity.agent_id)
                response_message = Message(
                    id=MessageId.generate(),
                    conversation_id=conversation.id,
                    sender_role=MessageRole.ASSISTANT,
                    content_type=MessageContentType.TEXT,
                    content=response_text,
                    channel_type=input.channel_type,
                    sent_at=datetime.now(tz=UTC),
                )
                await uow.messages.save(response_message)
                await self._channel_provider.send(response_message, opportunity)

            await uow.commit()

        if opportunity.attention_mode == AttentionMode.AI:
            await self._maybe_summarize(conversation.id)

        return opportunity

    async def _maybe_summarize(self, conversation_id: ConversationId) -> None:
        try:
            async with SQLAlchemyUnitOfWork(self._session_factory) as uow:
                previous = await uow.conversation_summaries.get_latest(conversation_id)
                since = previous.up_to_sent_at if previous else None
                count = await uow.messages.count_since(conversation_id, after=since)
                if count >= self._summary_trigger_messages:
                    await self._summarization_service.execute(conversation_id, uow)
                    await uow.commit()
        except Exception:
            logger.warning("summary.generation_failed", conversation_id=str(conversation_id))
```

El constructor de `ReceiveIncomingMessageUseCase` gana `context_assembler`,
`summarization_service` y `summary_trigger_messages`.

---

## 10. Corrección a Spec 005 — `AssignToAdvisorUseCase` / `ReturnToAIUseCase`

Ambos disparan el resumen **incondicionalmente** al final (evento de negocio, no de tamaño) —
un asesor humano que toma una conversación necesita un resumen actualizado aunque solo hayan
pasado 3 mensajes desde el último. Mismo patrón de segunda transacción + `try/except` que en la
sección 9:

```python
            opportunity.record_activity()
            await uow.opportunities.save(opportunity)
            await uow.commit()

        try:
            conversation = await self._get_conversation(opportunity.id)
            async with SQLAlchemyUnitOfWork(self._session_factory) as uow:
                await self._summarization_service.execute(conversation.id, uow)
                await uow.commit()
        except Exception:
            logger.warning("summary.generation_failed", opportunity_id=str(opportunity_id))

        return opportunity
```

Ambos casos de uso ganan `summarization_service` en el constructor.

---

## 11. Configuración — `app/config.py`

```python
    working_memory_size: int = 20
    summary_trigger_messages: int = 30
    summarization_model: str = "openai/gpt-4.1-nano"
```

Configurable por variable de entorno sin redeploy de código, tal como el resto de `Settings`.

---

## 12. Nuevo — `infrastructure/ai/openrouter.py`

`OpenRouterAIProvider` implementa `AIProvider`. Tal como quedó la firma en la sección 1,
`generate()` resuelve `agent_id` a `Agent` (vía un repositorio inyectado) para obtener `model` +
`system_prompt` — esto le da al provider una dependencia indirecta hacia `AgentRepository`. Es un
punto de fricción conocido y aceptado para 006 (ver ADR pendiente más abajo), no un descuido.
Arma el array de mensajes OpenAI-compatible anteponiendo el resumen (si existe) como parte del
system prompt, y llama al endpoint de chat completions de OpenRouter. `complete()` es más simple:
arma un mensaje `system` + `user` directo con el `model` del `CompletionRequest`, sin tocar ningún
`Agent` ni repositorio. Cliente HTTP: `httpx.AsyncClient`. Sin retry automático — un fallo se
propaga tal cual al caller (ver sección 9, ya lo trata como best-effort para el resumen; para
`generate()` en el flujo principal, el fallo sube como excepción no capturada, comportamiento a
definir explícitamente en la implementación).

## 13. Nuevo — `infrastructure/channels/telegram.py`

`TelegramChannelProvider` implementa `ChannelProvider`. `send()` recibe el `Contact` directo (ver
corrección en sección 1 — no se resuelve vía repositorio, el use case ya lo tiene en memoria) y
hace `POST` a `https://api.telegram.org/bot{token}/sendMessage` usando `Contact.external_id` como
`chat_id` (ya existe en la entidad desde spec 002/004, no requiere cambios ahí). `health()` hace
`GET .../getMe`. El provider queda completamente stateless — no recibe `session_factory` en su
constructor, no tiene ninguna razón para tocar la BD.

---

## ADR pendiente de evaluación durante implementación

No bloquea el inicio de 006. Se decide **al implementar** `OpenRouterAIProvider` (sección 12),
no antes — anotado aquí para no perderlo ni re-discutirlo desde cero.

**Actualización (post spec 007, prueba real de punta a punta):** el mismo acoplamiento en
`TelegramChannelProvider` sí complicó el código en la práctica — ver corrección en la sección 1.
Queda como evidencia a favor de aplicar el mismo cambio aquí, en `OpenRouterAIProvider`, aunque
el riesgo es menor: `Agent` nunca se crea en la misma transacción que lo consulta (siempre
preexiste, sembrado o gestionado por separado), así que no puede darse el mismo bug de
lectura-antes-de-commit. El ADR de abajo sigue sin resolverse para este provider específicamente.

**Contexto.** `AIProvider.generate(context, agent_id)` obliga al provider a resolver
`agent_id → Agent` para obtener `model` + `system_prompt`. Eso le da al provider una dependencia
indirecta hacia `AgentRepository` — un adaptador a un servicio externo (OpenRouter) terminando
por conocer un repositorio del dominio. Rompe parcialmente el aislamiento que se buscó al separar
`complete()` de las tareas de negocio en la sección de Principio Arquitectónico.

**Alternativa evaluada.** Que el servicio de aplicación resuelva `Agent` *antes* de llamar al
provider, y le pase un objeto ya armado:

```python
@dataclass(frozen=True)
class ConversationRequest:
    model: str
    system_prompt: str
    context: ConversationContext
```

con `generate(request: ConversationRequest) -> str`. El provider deja de tocar cualquier
repositorio — queda completamente stateless y más fácil de testear con fakes (no requiere mockear
`AgentRepository` para probar el prompt de conversación).

**Decisión.** No se adopta en 006. Se mantiene `generate(context, agent_id)` tal como quedó en la
sección 1. Se revisita si, al escribir `OpenRouterAIProvider`, el acoplamiento a
`AgentRepository` complica el código en la práctica — no antes, y no especulativamente.

**Relacionado, mismo momento de revisión.** Separar también la construcción del prompt
(`ConversationPromptFactory` / `ChatPrompt`) del provider, para que cambiar de proveedor (OpenAI,
Anthropic, Gemini) no obligue a tocar cómo se arman los prompts. Anotado como evolución posible,
no se implementa en 006.

---

## Future Evolution (Not part of this specification)

Registro de decisiones deliberadamente postergadas — no un backlog, un recordatorio de que ya se
discutieron y no deben re-litigarse sin evidencia nueva.

| Spec | Alcance | Se aborda cuando... |
|---|---|---|
| 007 — API Layer | Routers FastAPI (webhook Telegram, gestión de oportunidades) + `app/dependencies.py` | Inmediato — siguiente spec |
| 008 — Memory Extraction | `CustomerMemory` (preferencias, datos comerciales) extraído por LLM, persistido estructurado, sin búsqueda semántica | Exista una necesidad comercial concreta, no antes |
| 009 — Knowledge Base | Unificar catálogo, PDFs, Excel, reglas de negocio, precios, FAQs como fuente única | El agente necesite responder con info que hoy no tiene |
| 010 — AI Task Framework | Tareas más allá del chat (clasificación de intención, cotización, calificación de leads) reutilizando `complete()` | Aparezca una segunda tarea de IA real además de conversar/resumir |
| 011 — Embedding Search | `EmbeddingProvider` + `ConversationRetriever`, sin tocar `AIProvider`/`ConversationContextAssembler`/`ConversationSummary` | El volumen de conocimiento no quepa razonablemente en un resumen o prompt |
| 012 — Background Jobs | Celery/Redis/Temporal; mover generación de resumen y extracción a async | La latencia o el volumen de resúmenes síncronos se vuelva un problema medido, no anticipado |
| 013 — Model Routing | Explotar `complete()` para enrutar cada tarea a un modelo distinto por costo/calidad | Ya lo permite el diseño actual de `CompletionRequest.model` — solo falta la política de ruteo |
| 014 — Prompt Management | Prompts fuera de Python, versionados, editables, A/B testing | Los prompts cambien con frecuencia suficiente para justificar tooling dedicado |
| 015 — Context Optimization | Compresión de contexto, resúmenes jerárquicos, recuperación híbrida, estrategias adaptativas por modelo | Conversaciones largas (miles de mensajes) hagan insuficiente el resumen plano de 006 |

Nota: se consolidó en un solo ítem (008) lo que en la discusión previa aparecía como dos entradas
separadas ("Memory Extraction" mencionada dos veces) — mismo alcance, una sola entrada.

---

## Próximo paso

Spec 007 — API Layer: routers FastAPI + wiring de dependencias, consumiendo todo lo construido
en 006 (`AIProvider`, `ChannelProvider`, `ConversationContextAssembler`,
`ConversationSummarizationService`).
