# 010 Advisor Reply

## Propósito

Gap encontrado en validación manual del Advisor Workspace (spec 009): un asesor puede **tomar**
una conversación y **devolverla a IA**, pero no tiene forma de escribirle al cliente. El workspace
hoy es de solo lectura para el humano — puede ver el historial, pero no participar en él. Esto se
detectó antes de arrancar el piloto operativo con Amza Empaques (ver `PROJECT_STATE.md`), y es más
urgente que el piloto mismo: sin esto, tomar una conversación no tiene ningún efecto observable
para el cliente.

**Regla de negocio, explícita desde el principio de este spec:** un asesor solo puede enviar un
mensaje manual cuando la oportunidad está en modo `HUMAN` **y** asignada a ese asesor específico.
Si está en modo `AI`, o asignada a otro asesor, el intento de envío falla — no hay excepción para
"cualquier asesor autenticado puede escribir en cualquier oportunidad".

**Explícitamente fuera de alcance:** adjuntos/imágenes (solo texto, igual que el resto de la
plataforma hasta ahora), edición o borrado de mensajes ya enviados, indicador de "escribiendo...",
reasignación automática al enviar (el asesor ya tuvo que tomar la conversación primero, spec 009).

---

## 1. Nuevo — `MessageRole.ADVISOR`

`core/enums/message.py`:

```python
class MessageRole(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    ADVISOR = "advisor"
    SYSTEM = "system"
```

Sin migración: `messages.sender_role` ya es `VARCHAR(50)` sin `CHECK` a nivel de BD
(`modules/opportunities/models/message.py`) — el enum vive solo en Python. Distinguir `ADVISOR` de
`ASSISTANT` importa para el historial: hoy ambos se ven idénticos en la UI (mismo lado, spec 009),
y un asesor revisando una conversación necesita saber si esa respuesta la escribió la IA o un
humano.

---

## 2. Nueva excepción de dominio — `OpportunityNotAssignedToAdvisorError`

`core/exceptions/domain.py`:

```python
class OpportunityNotAssignedToAdvisorError(DomainError):
    def __init__(self, opportunity_id: OpportunityId, advisor_id: InternalUserId) -> None:
        super().__init__(
            f"Opportunity {opportunity_id} is not assigned to advisor {advisor_id}"
        )
        self.opportunity_id = opportunity_id
        self.advisor_id = advisor_id
```

**Un solo chequeo cubre los dos casos de la regla de negocio:** `opportunity.assigned_advisor_id
!= advisor_id`. `Opportunity.assign_to_advisor()` y `Opportunity.return_to_ai()`
(`core/entities/opportunity.py`) siempre fijan/limpian `attention_mode` y `assigned_advisor_id`
juntos — nunca hay un estado donde `attention_mode == HUMAN` con `assigned_advisor_id == None`, ni
viceversa. Por eso comparar solo `assigned_advisor_id` ya distingue "sigue en modo IA" (es `None`,
nunca igual a un `advisor_id` real) de "está asignada a otro asesor", sin necesitar dos
excepciones ni leer `attention_mode` aparte.

`app/exceptions.py` — se agrega a `_UNPROCESSABLE_ERRORS` (422, mismo trato que
`InvalidStatusTransitionError`: es una regla de negocio violada, no un recurso inexistente).

---

## 3. Nuevo caso de uso — `SendAdvisorReplyUseCase`

`app/use_cases/send_advisor_reply.py`:

```python
from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.entities.message import Message
from core.enums.message import MessageContentType, MessageRole
from core.exceptions.domain import (
    ContactNotFoundError,
    OpportunityNotAssignedToAdvisorError,
    OpportunityNotFoundError,
)
from core.interfaces.providers import ChannelProvider
from core.value_objects.identifiers import InternalUserId, MessageId, OpportunityId
from infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork


class SendAdvisorReplyUseCase:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        channel_provider: ChannelProvider,
    ) -> None:
        self._session_factory = session_factory
        self._channel_provider = channel_provider

    async def execute(
        self,
        opportunity_id: OpportunityId,
        advisor_id: InternalUserId,
        content: str,
    ) -> Message:
        async with SQLAlchemyUnitOfWork(self._session_factory) as uow:
            opportunity = await uow.opportunities.get_by_id(opportunity_id)
            if opportunity is None:
                raise OpportunityNotFoundError(opportunity_id)

            if opportunity.assigned_advisor_id != advisor_id:
                raise OpportunityNotAssignedToAdvisorError(opportunity_id, advisor_id)

            conversation = await uow.conversations.get_by_opportunity(opportunity.id)
            assert conversation is not None  # invariante: toda Opportunity asignada ya tiene Conversation

            contact = await uow.contacts.get_by_id(opportunity.contact_id)
            if contact is None:
                raise ContactNotFoundError(opportunity.contact_id)

            message = Message(
                id=MessageId.generate(),
                conversation_id=conversation.id,
                sender_role=MessageRole.ADVISOR,
                content_type=MessageContentType.TEXT,
                content=content,
                channel_type=opportunity.channel_type,
                sent_at=datetime.now(tz=UTC),
            )
            await uow.messages.save(message)

            opportunity.record_activity()
            await uow.opportunities.save(opportunity)

            await self._channel_provider.send(message, contact)

            await uow.commit()

        return message
```

Mismo patrón que `ReceiveIncomingMessageUseCase` (spec 006): el mensaje se persiste y se entrega
por `ChannelProvider.send()` **dentro** de la misma transacción, antes del `commit()` final — si
el envío a Telegram falla, la transacción completa hace rollback en vez de dejar un mensaje
persistido que nunca llegó al cliente.

**Sin resumen incondicional aquí, a diferencia de `assign_to_advisor`/`return_to_ai`.** Esos dos
disparan un resumen porque son puntos de *transferencia de contexto* (IA→humano, humano→IA). Un
mensaje individual del asesor no cambia quién atiende — cuando eventualmente se devuelva a IA,
`ReturnToAIUseCase` ya genera un resumen que cubre todo lo ocurrido desde el último, incluyendo
estos mensajes. No hace falta duplicar esa lógica aquí.

`ChannelProvider.send()` no cambia de firma — ya recibe `Message` + `Contact` genéricos (spec 006,
corregido tras el bug real documentado ahí); no le importa si el mensaje lo originó la IA o un
humano.

---

## 4. Nuevo endpoint — `POST /organizations/{slug}/opportunities/{id}/messages`

`app/api/dto/opportunity.py` — nuevo DTO, junto a los existentes:

```python
class SendMessageRequest(BaseModel):
    advisor_id: str
    content: str
```

`app/api/routers/opportunities.py` — mismo router protegido, mismo patrón que
`assign-advisor`/`return-to-ai`:

```python
@router.post("/{opportunity_id}/messages")
async def send_advisor_reply(
    organization_slug: str,  # ignorado intencionalmente, ver nota de alcance en spec 007
    opportunity_id: str,
    body: SendMessageRequest,
    use_case: SendAdvisorReplyUseCase = Depends(get_send_advisor_reply_use_case),
) -> MessageResponse:
    message = await use_case.execute(
        OpportunityId.from_string(opportunity_id),
        InternalUserId.from_string(body.advisor_id),
        body.content,
    )
    return MessageResponse.from_domain(message)
```

`advisor_id` viaja en el body, no se deriva de la sesión — mismo criterio ya establecido por
`assign-advisor` en spec 009 (el frontend lo llena con `currentUser.id`). No es una decisión nueva
de este spec.

`app/dependencies.py`:

```python
@lru_cache
def get_send_advisor_reply_use_case() -> SendAdvisorReplyUseCase:
    return SendAdvisorReplyUseCase(
        session_factory=AsyncSessionFactory,
        channel_provider=get_channel_provider(),
    )
```

---

## 5. Frontend — enviar mensaje desde `/opportunities/[id]`

`frontend/hooks/use-send-message.ts` (nuevo):

```typescript
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/services/api";
import type { Message } from "@/types/api";

interface SendMessageArgs {
  organizationSlug: string;
  opportunityId: string;
  advisorId: string;
  content: string;
}

export function useSendMessage() {
  const queryClient = useQueryClient();

  return useMutation<Message, Error, SendMessageArgs>({
    mutationFn: ({ organizationSlug, opportunityId, advisorId, content }) =>
      apiFetch<Message>(
        `/api/organizations/${organizationSlug}/opportunities/${opportunityId}/messages`,
        { method: "POST", body: JSON.stringify({ advisor_id: advisorId, content }) },
      ),
    onSuccess: (_data, { organizationSlug, opportunityId }) => {
      // invalidateQueries alcanza aquí -- a diferencia de useAssignToAdvisor/useReturnToAI
      // (hooks/use-opportunity-actions.ts), esta página sigue montada con un observador activo
      // sobre conversationHistory cuando la mutación resuelve: el refetch ocurre de inmediato, sin
      // la ventana de dato viejo que sí existía para la lista de oportunidades.
      queryClient.invalidateQueries({
        queryKey: ["conversationHistory", organizationSlug, opportunityId],
      });
    },
  });
}
```

`frontend/app/opportunities/[id]/page.tsx` — agregar textarea + botón, visibles solo cuando
`isMine` (que ya implica `attention_mode === "human"`, por el mismo invariante de la sección 2):

```tsx
const sendMessage = useSendMessage();
const [draft, setDraft] = useState("");

// ...dentro del render, junto al botón "Devolver a IA":
{isMine && (
  <form
    onSubmit={(e) => {
      e.preventDefault();
      if (!draft.trim()) return;
      sendMessage.mutate(
        {
          organizationSlug: currentUser.organization_slug,
          opportunityId: opportunity.id,
          advisorId: currentUser.id,
          content: draft,
        },
        { onSuccess: () => setDraft("") },
      );
    }}
    className="mt-4 flex gap-2"
  >
    <input
      value={draft}
      onChange={(e) => setDraft(e.target.value)}
      placeholder="Escribe tu respuesta..."
      className="flex-1 rounded border px-3 py-2"
      disabled={sendMessage.isPending}
    />
    <button
      type="submit"
      disabled={sendMessage.isPending || !draft.trim()}
      className="rounded bg-foreground px-4 py-2 text-background disabled:opacity-50"
    >
      {sendMessage.isPending ? "Enviando..." : "Enviar"}
    </button>
  </form>
)}
```

`draft` es estado propio del formulario (lo que el usuario está escribiendo), no una copia de
datos del servidor — no viola la regla de spec 009 de "sin estado derivado", esa regla aplica a
datos que ya vienen de `useQuery()`.

---

## 6. Corrección necesaria — `OpenRouterAIProvider.generate()` no puede seguir usando `sender_role.value` como rol de la API

`infrastructure/ai/openrouter.py` arma hoy el payload de OpenRouter así (línea 49-53), con un
comentario que ya no es cierto una vez existe `MessageRole.ADVISOR`:

```python
# MessageRole.value ("user"/"assistant"/"system") ya coincide con los roles OpenAI-compatibles
# que espera OpenRouter — no hace falta mapeo.
...
messages.extend(
    {"role": m.sender_role.value, "content": m.content}
    for m in context.recent_messages
)
```

Si un mensaje con `sender_role=ADVISOR` cae dentro de la ventana de `working_memory_size` cuando
la conversación vuelve a modo IA (`ReturnToAIUseCase` no vacía el historial, solo cambia
`attention_mode`), este código mandaría `{"role": "advisor", ...}` — un rol que la API de
OpenRouter/OpenAI no reconoce, y la llamada fallaría.

**Fix:** mapear explícitamente `ADVISOR` → `"assistant"` al armar el payload — desde el punto de
vista del modelo, el turno de un asesor humano *es* el turno del "assistant" en el diálogo (todo
lo que no es el cliente).

```python
_TO_OPENAI_ROLE = {
    MessageRole.USER: "user",
    MessageRole.ASSISTANT: "assistant",
    MessageRole.ADVISOR: "assistant",
    MessageRole.SYSTEM: "system",
}

...

messages.extend(
    {"role": _TO_OPENAI_ROLE[m.sender_role], "content": m.content}
    for m in context.recent_messages
)
```

El resumen (`conversation_summarization_service.py`) no necesita este mapeo — ahí `sender_role.value`
se usa como texto plano dentro del transcript (`"advisor: ..."`), no como un rol de API, así que
un modelo leyéndolo como resumen no tiene problema en distinguir "advisor" de "assistant" en ese
contexto.

---

## 7. Tests

Política vigente desde spec 008: este spec incluye pruebas de lo que introduce.

- Backend (`tests/test_security_and_identity.py` o un archivo nuevo
  `tests/test_advisor_reply.py`): tres escenarios —
  1. Asesor asignado envía mensaje → 200, mensaje persistido con `sender_role="advisor"`,
     `channel_provider.send()` invocado (fake/spy).
  2. Oportunidad todavía en modo `AI` (nadie la tomó) → 422.
  3. Oportunidad asignada a **otro** asesor → 422 (mismo código, mismo `assigned_advisor_id !=
     advisor_id`).
- Backend, regresión específica de la sección 6 (`tests/test_openrouter_provider.py` o donde ya
  viva la cobertura de `OpenRouterAIProvider`): `generate()` con un `ConversationContext` que
  incluya un mensaje `sender_role=ADVISOR` en `recent_messages` → el payload enviado a OpenRouter
  (capturado vía fake `httpx` transport) debe llevar `"role": "assistant"` para ese mensaje, nunca
  `"role": "advisor"`. Este es el escenario real que dispara el fix de la sección 6: un asesor
  responde, se devuelve a IA, y ese mensaje sigue dentro de `working_memory_size`.
- Frontend (`frontend/tests/e2e/advisor-workspace.spec.ts`): extender el flujo existente —
  después de tomar la conversación, escribir un mensaje, confirmar que aparece en el historial con
  el rol correcto.

---

## Próximo paso

Con esto, el Advisor Workspace deja de ser de solo lectura para el humano — recién ahí tiene
sentido retomar **"Pilot Validation"** con Amza Empaques (ver spec 009, sección final): definir
criterios de éxito antes de empezar, sin tocar todavía el roadmap especulativo (Knowledge Base,
Embeddings, Background Jobs, etc.).
