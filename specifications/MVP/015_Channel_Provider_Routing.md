# 015 Channel Provider Routing

## Propósito

Este spec estaba planeado como "Contact Channel Tagging" — una etiqueta de canal en `Contact`
para identificar de dónde viene cada cliente, como prerrequisito de spec 016 (WhatsApp
Integration). Al investigar antes de escribirla, resultó que **esa parte ya existe**:
`Contact.channel_type`/`Opportunity.channel_type` son campos del dominio desde spec 002, y spec
012 ya los usa para el chip de Telegram/WhatsApp en la lista y el encabezado del chat. No hay
ninguna etiqueta que agregar.

El prerrequisito real de spec 016 es otro, y se encontró revisando cómo se entrega un mensaje
saliente hoy: `app/dependencies.py::get_channel_provider()` construye **un solo**
`ChannelProvider`, siempre `TelegramChannelProvider`, y ese único objeto se inyecta tanto en
`ReceiveIncomingMessageUseCase` como en `SendAdvisorReplyUseCase`. Funciona hoy porque solo existe
un canal real. En el momento en que exista un `Contact` de WhatsApp, `POST
.../opportunities/{id}/messages` (el mismo endpoint genérico para responder, sin importar el
canal) seguiría intentando enviar por la API de Telegram — silenciosamente mal, no un error
obvio. Este spec construye el mecanismo de selección **antes** de que spec 016 agregue el segundo
proveedor, para que esa spec no tenga que tocar ninguno de los dos casos de uso.

Se renombra el spec de "Contact Channel Tagging" a **"Channel Provider Routing"** porque el
título anterior ya no describe lo que realmente hace — mismo criterio de honestidad que ya se
aplicó al reordenar specs 012/013.

**Explícitamente fuera de alcance:** la implementación real de `WhatsAppChannelProvider` (spec
016); permitir más de un `ChannelProvider` activo por canal simultáneamente (no hay ningún caso de
negocio para eso); cualquier cambio a `Contact`/`Opportunity` — ambos ya tienen todo lo que este
spec necesita.

---

## 1. `ChannelProviderRegistry`

No es un `Protocol` nuevo — es una clase concreta de composición, no un puerto hacia
infraestructura externa (ese test ya lo satisface `ChannelProvider`, que sigue como Protocol sin
cambios). `app/services/channel_provider_registry.py` (nuevo, mismo directorio que
`ConversationContextAssembler`/`ConversationSummarizationService` — servicios de aplicación
concretos, no puertos):

```python
from __future__ import annotations

from core.enums.channel import ChannelType
from core.exceptions.domain import UnsupportedChannelError
from core.interfaces.providers import ChannelProvider


class ChannelProviderRegistry:
    def __init__(self, providers: dict[ChannelType, ChannelProvider]) -> None:
        self._providers = providers

    def get(self, channel_type: ChannelType) -> ChannelProvider:
        provider = self._providers.get(channel_type)
        if provider is None:
            raise UnsupportedChannelError(channel_type)
        return provider

    def all(self) -> dict[ChannelType, ChannelProvider]:
        return dict(self._providers)
```

`core/exceptions/domain.py` — nueva excepción:

```python
class UnsupportedChannelError(DomainError):
    def __init__(self, channel_type: ChannelType) -> None:
        super().__init__(f"No ChannelProvider registered for channel {channel_type.value!r}")
```

**Deliberadamente sin bucket en `app/exceptions.py`** (ni `_NOT_FOUND_ERRORS`, ni
`_UNPROCESSABLE_ERRORS`, ni `_FORBIDDEN_ERRORS`) — cae en el manejador genérico de `DomainError`
(400, con `logger.warning("domain.error.unhandled", ...)`). No es un error de negocio del usuario
(nadie eligió un canal inválido desde la UI — `ChannelType` ya se valida en la frontera del
webhook), es un error de **configuración**: alguien agregó un canal nuevo al dominio sin registrar
su provider en `app/dependencies.py`. El log de advertencia con el mensaje específico es
suficiente para diagnosticarlo; no vale la pena una categoría HTTP nueva para un caso que, si
ocurre, es un bug de despliegue, no una respuesta esperada del usuario.

---

## 2. `ReceiveIncomingMessageUseCase` y `SendAdvisorReplyUseCase` — reciben el registro, no un provider

`app/use_cases/receive_incoming_message.py` — el constructor cambia de `channel_provider:
ChannelProvider` a `channel_provider_registry: ChannelProviderRegistry`; el único punto de envío
(línea 147 hoy) resuelve el provider correcto en el momento de enviar:

```python
# antes
await self._channel_provider.send(response_message, contact)

# ahora
provider = self._channel_provider_registry.get(contact.channel_type)
await provider.send(response_message, contact)
```

`app/use_cases/send_advisor_reply.py` — mismo cambio, mismo punto (línea 64 hoy):

```python
# antes
await self._channel_provider.send(message, contact)

# ahora
provider = self._channel_provider_registry.get(contact.channel_type)
await provider.send(message, contact)
```

Se resuelve por `contact.channel_type`, no por `opportunity.channel_type` — son el mismo valor
hoy (`Contact.get_by_external_id()` ya filtra por `channel_type`, spec 002), pero `contact` es el
objeto que realmente se le pasa a `provider.send()`, así que leer el canal de ahí mismo es más
directo y evita depender de que ambos campos sigan sincronizados por convención en vez de por
tipo.

Ningún otro cambio en ninguno de los dos casos de uso — su lógica de negocio no se toca, solo de
dónde sale el `ChannelProvider` que ya usaban.

---

## 3. `app/dependencies.py` — un registro en vez de un provider

```python
# antes
@lru_cache
def get_channel_provider() -> ChannelProvider:
    return TelegramChannelProvider(bot_token=settings.telegram_bot_token)

# ahora
@lru_cache
def get_channel_provider_registry() -> ChannelProviderRegistry:
    return ChannelProviderRegistry({
        ChannelType.TELEGRAM: TelegramChannelProvider(bot_token=settings.telegram_bot_token),
    })
```

`get_receive_incoming_message_use_case()` y `get_send_advisor_reply_use_case()` pasan
`channel_provider_registry=get_channel_provider_registry()` en vez de
`channel_provider=get_channel_provider()`. Cuando spec 016 agregue `WhatsAppChannelProvider`, el
único cambio en este archivo es una línea más en el diccionario — ninguno de los dos casos de uso
se vuelve a tocar. Este es exactamente el resultado que justifica haber escrito este spec antes de
016 en vez de descubrir el problema ahí.

---

## 4. `/health/ready` — generalizado a "todos los canales registrados"

`app/api/routers/health.py` hoy reporta una sola clave fija `"telegram"`. Con el registro, se
generaliza a iterar lo que esté registrado, sin necesitar tocar este archivo cuando se agregue un
canal nuevo:

```python
@router.get("/ready")
async def readiness(
    ai_provider: AIProvider = Depends(get_ai_provider),
    channel_registry: ChannelProviderRegistry = Depends(get_channel_provider_registry),
) -> JSONResponse:
    checks: dict[str, bool] = {}

    try:
        async with AsyncSessionFactory() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception:
        checks["database"] = False

    checks["openrouter"] = await ai_provider.health()
    for channel_type, provider in channel_registry.all().items():
        checks[channel_type.value] = await provider.health()

    status_code = 200 if all(checks.values()) else 503
    return JSONResponse(status_code=status_code, content=checks)
```

Respuesta hoy (un solo canal registrado): `{"database": true, "openrouter": true, "telegram":
true}` — idéntica a la actual, ningún consumidor externo de este endpoint se rompe.

---

## 5. Tests

Política vigente desde spec 008: este spec incluye pruebas de lo que introduce.

- `tests/test_channel_provider_registry.py` (nuevo):
  1. `registry.get(ChannelType.TELEGRAM)` devuelve el provider registrado para ese canal.
  2. `registry.get(ChannelType.WHATSAPP)` (sin registrar todavía) → `UnsupportedChannelError`.
  3. `registry.all()` devuelve una copia — mutar el diccionario devuelto no afecta al registro
     interno.
- Regresión en las suites existentes de `ReceiveIncomingMessageUseCase`/`SendAdvisorReplyUseCase`
  (`tests/test_openrouter_provider.py` y donde viva la cobertura de spec 010): reemplazar el fake
  `ChannelProvider` inyectado directo por un `ChannelProviderRegistry` de una sola entrada — el
  comportamiento observado (qué `Message`/`Contact` recibe `.send()`) no cambia, solo cómo se
  construye el caso de uso en el test.
- `GET /health/ready` — sigue devolviendo `telegram: true/false` con un solo canal registrado
  (regresión explícita: nadie rompió el shape de esta respuesta al generalizarla).

---

## Próximo paso

Spec 016 — **WhatsApp Integration (Evolution API)**: `WhatsAppChannelProvider` (implementa el
mismo `ChannelProvider` Protocol, sin cambios ahí), registrado en
`get_channel_provider_registry()` junto al de Telegram, más el webhook, el ritmo anti-baneo
(pausas aleatorias, retraso de primera respuesta), el manejo de la ventana de 24h como regla de
producto/UI (no técnica — decisión ya registrada en `PROJECT_STATE.md`), y la conexión por código
QR.
