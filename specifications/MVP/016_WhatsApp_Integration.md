# 016 WhatsApp Integration (Evolution API)

## Propósito

Segundo canal real de la plataforma (spec 015 dejó listo el mecanismo de selección —
`ChannelProviderRegistry` — precisamente para que agregar este spec fuera solo eso: agregar un
proveedor, no tocar los casos de uso). Se integra vía **Evolution API**
(self-hosted, no oficial — un wrapper HTTP sobre la librería que habla el protocolo de WhatsApp
Web), con el número **+57 301 509 2386**.

**No es solo "otro `ChannelProvider`".** Al ser una API no oficial, el riesgo real no es técnico
sino de **baneo del número** — WhatsApp detecta patrones de bot (mensajes instantáneos, ritmo
perfectamente regular, nunca "escribe...", nunca lee lo que le llega) y puede bloquear la cuenta.
La mayor parte de este spec es exactamente la mitigación de ese riesgo, no la integración en sí
— que, mecánicamente, es la misma forma que ya tiene `TelegramChannelProvider`.

**Fuentes verificadas contra la documentación real de Evolution API** (no asumidas de memoria —
se consultó `https://docs.evolutionfoundation.com.br/` antes de escribir este spec): endpoints de
envío de texto, configuración de webhook, estado de conexión, creación de instancia y marcar
mensaje como leído. Donde la documentación no fue concluyente (dos puntos, marcados
explícitamente abajo), se deja anotado para confirmar en implementación en vez de asumir.

**Explícitamente fuera de alcance:**

- Pantalla de conexión/QR en `/admin` — spec 017 (Admin Panel) es donde se decidió que vive esa
  UI. Este spec deja el **script** de aprovisionamiento (sección 5), igual que Telegram nunca tuvo
  UI de registro de webhook, solo un script (`register_telegram_webhook.py`, spec 007).
- Descargar/almacenar archivos multimedia recibidos (fotos, audios, PDF) — Media Library, más
  adelante en esta tanda. Se muestran igual que spec 012 ya decidió para cualquier canal: una
  tarjeta con el tipo, no el contenido real.
- Variar el texto de las respuestas de la IA para no repetir plantillas — es una instrucción sobre
  el *contenido* del prompt del agente, no sobre el canal; corresponde a quien escriba/edite el
  `system_prompt` (editable desde spec 017), no a este spec.
- Advertencia de "ventana de 24h" en la UI — **no necesita nada de este spec**: el frontend ya
  tiene `sent_at` de cada mensaje (spec 012); calcular "han pasado más de 24h desde el último
  mensaje del cliente" es aritmética client-side sobre datos que ya existen. Se implementa cuando
  se construya la UI que lo necesite, no aquí.
- Aplicar un límite de tasa explícito contra los ~80 mensajes/segundo que documenta Evolution API
  — el ritmo anti-baneo de este spec (segundos entre envíos, nunca milisegundos) ya deja el
  tráfico real varios órdenes de magnitud por debajo de ese límite. No hace falta un limitador
  aparte para un límite que nunca se puede alcanzar con este diseño.

---

## 1. El problema arquitectónico real: `send()` no puede seguir bloqueando dentro de la transacción

`ReceiveIncomingMessageUseCase`/`SendAdvisorReplyUseCase` llaman
`await channel_provider.send(message, contact)` **dentro** de la transacción que persiste el
mensaje (decisión de spec 006: si el envío falla, todo hace rollback). Con Telegram eso tarda
milisegundos. Con el ritmo anti-baneo que este spec necesita (30 segundos en el primer mensaje de
una conversación, 2-15 segundos aleatorios después, más una separación mínima entre envíos
consecutivos) esa misma llamada podría tardar hasta 30+ segundos — y SQLite con un solo escritor
no tolera una transacción abierta ese tiempo mientras llegan otros webhooks o acciones de asesor.

**No se cambia esa garantía para Telegram** (seguiría siendo una regresión no pedida). La
solución es que `WhatsAppChannelProvider.send()` en sí mismo sea **no bloqueante**: encola el
envío y retorna casi de inmediato; el ritmo real (esperar, "escribir", enviar) ocurre después, en
un worker en segundo plano que vive todo el tiempo que vive la aplicación — no un
`asyncio.create_task()` por request (ese patrón se descartó explícitamente en spec 006: "sin cola
de tareas ni supervisión, una excepción se traga en silencio"). Aquí sí hay una cola
(`asyncio.Queue`, en memoria) y un único worker supervisado, arrancado una vez en el ciclo de vida
de la aplicación — es la pieza que le faltaba a aquel razonamiento, no una excepción a él.

**Riesgo aceptado, mismo espíritu que "sin cola de reintentos para fallos de infraestructura"**
(ya en la tabla de Production Risks): la cola vive en memoria del proceso. Si el proceso se cae
con mensajes encolados sin enviar todavía, esos mensajes se pierden — ya están persistidos en la
base de datos (la transacción principal ya hizo `commit()` antes de que el worker los procese),
pero el cliente nunca los recibió. Aceptado para MVP; se revisita si en la práctica llega a
importar.

---

## 2. `ChannelProvider.send()` — un parámetro nuevo, con default, no rompe a Telegram

`core/interfaces/providers.py`:

```python
class ChannelProvider(Protocol):
    async def send(self, message: Message, contact: Contact, *, is_first_reply: bool = False) -> None: ...
    async def health(self) -> bool: ...
```

`is_first_reply` lo usa la IA para decir "esta es la primera respuesta automática de esta
conversación" — `TelegramChannelProvider.send()` gana el parámetro en su firma y lo ignora
(ningún cambio de comportamiento). Quién decide **qué hacer** con `is_first_reply` es el
proveedor, no el caso de uso — `WhatsAppChannelProvider` combina esa bandera con
`message.sender_role` (ya presente en `Message`, sin cambios ahí) para decidir el retraso:

| `message.sender_role` | `is_first_reply` | Retraso simulado antes de enviar |
|---|---|---|
| `ASSISTANT` (respuesta de IA) | `True` | 30 segundos fijos |
| `ASSISTANT` (respuesta de IA) | `False` | aleatorio entre 2 y 15 segundos |
| `ADVISOR` (asesor humano) | (no aplica) | 0 — un humano que decidió enviar ya es el comportamiento que se busca simular, retrasarlo no aporta nada |

`ReceiveIncomingMessageUseCase` es quien calcula `is_first_reply` (tiene el conteo de mensajes a
mano; el proveedor no debería necesitar consultar la base de datos para esto — mismo principio
que ya corrigió el bug real de `TelegramChannelProvider` en spec 006, los providers no resuelven
nada por su cuenta):

```python
message_count = await uow.messages.count_since(conversation.id, after=None)
is_first_reply = message_count == 1  # solo existe el mensaje entrante que se acaba de guardar
...
provider = self._channel_provider_registry.get(contact.channel_type)
await provider.send(response_message, contact, is_first_reply=is_first_reply)
```

`SendAdvisorReplyUseCase` no cambia — no pasa `is_first_reply`, usa el default `False`, y como su
`message.sender_role` siempre es `ADVISOR`, `WhatsAppChannelProvider` nunca le aplica retraso
simulado de todos modos.

---

## 3. `WhatsAppChannelProvider` — cola, worker, y las llamadas reales a Evolution API

`infrastructure/channels/whatsapp.py` (nuevo, mismo directorio que `telegram.py`):

```python
import asyncio
import random
import time
from dataclasses import dataclass

import httpx

from core.entities.contact import Contact
from core.entities.message import Message
from core.enums.message import MessageRole


@dataclass(frozen=True)
class _QueuedSend:
    message: Message
    contact: Contact
    typing_delay_seconds: float


class WhatsAppChannelProvider:
    _MIN_GAP_RANGE = (2.0, 5.0)       # "pausas aleatorias... entre cada mensaje"
    _FIRST_REPLY_DELAY = 30.0         # "el primer mensaje... tardarás 30 segundos"
    _REPLY_DELAY_RANGE = (2.0, 15.0)  # "2-15 segundos aleatorios" en adelante

    def __init__(self, base_url: str, api_key: str, instance_name: str) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers={"apikey": api_key},
        )
        self._instance_name = instance_name
        self._queue: asyncio.Queue[_QueuedSend] = asyncio.Queue()
        self._worker_task: asyncio.Task[None] | None = None
        self._last_sent_at: float = 0.0

    def start(self) -> None:
        """Llamado una vez en app/lifecycle.py -- no por request."""
        self._worker_task = asyncio.create_task(self._run_worker())

    async def stop(self) -> None:
        if self._worker_task is not None:
            self._worker_task.cancel()

    async def send(self, message: Message, contact: Contact, *, is_first_reply: bool = False) -> None:
        delay = 0.0
        if message.sender_role == MessageRole.ASSISTANT:
            delay = self._FIRST_REPLY_DELAY if is_first_reply else random.uniform(*self._REPLY_DELAY_RANGE)
        await self._queue.put(_QueuedSend(message, contact, delay))

    async def _run_worker(self) -> None:
        while True:
            item = await self._queue.get()
            await asyncio.sleep(item.typing_delay_seconds)

            min_gap = random.uniform(*self._MIN_GAP_RANGE)
            elapsed = time.monotonic() - self._last_sent_at
            if elapsed < min_gap:
                await asyncio.sleep(min_gap - elapsed)

            await self._send_now(item.message, item.contact)
            self._last_sent_at = time.monotonic()

    async def _send_now(self, message: Message, contact: Contact) -> None:
        response = await self._client.post(
            f"/message/sendText/{self._instance_name}",
            json={
                "number": contact.external_id,
                "textMessage": {"text": message.content},
                "delay": 0,  # el ritmo ya lo controlamos nosotros, ver nota abajo
            },
        )
        response.raise_for_status()

    async def health(self) -> bool:
        try:
            response = await self._client.get(f"/instance/connectionState/{self._instance_name}")
        except httpx.HTTPError:
            return False
        if response.status_code != httpx.codes.OK:
            return False
        return response.json().get("instance", {}).get("state") == "open"
```

**`"delay": 0` en el body de `sendText` es deliberado, no un olvido:** Evolution API expone su
propio campo `delay` (en milisegundos) para retrasar el envío. Se decide **no** usarlo y controlar
el ritmo enteramente en nuestro lado (el worker de arriba) por dos razones: (1) la documentación
no aclara si ese `delay` bloquea la respuesta HTTP de Evolution API o se resuelve del lado de
ellos de forma asíncrona — depender de un comportamiento no confirmado es más riesgoso que
controlarlo nosotros; (2) el "leer" + "escribiendo..." (ver nota siguiente) también necesita
orquestarse desde nuestro lado, así que el ritmo tiene que vivir aquí de todos modos.

**Pendiente de confirmar en implementación, no asumido:** si Evolution API (a diferencia del
producto hermano "Evolution Go") expone un endpoint de presencia (`escribiendo...`) para la
familia "Evolution API" específicamente — la documentación solo confirmó ese endpoint para
"Evolution Go". Si existe, `_send_now()` debería enviar presencia `composing` antes del mensaje y
`paused` después, reforzando el requisito de "no solo enviar texto, simular que escribe". Si no
existe, el retraso ya construido (sección 2) sigue siendo la mitigación real — la presencia sería
una mejora, no el mecanismo principal. No bloquea este spec, se confirma al implementar.

**Marcar el mensaje entrante como leído** (`POST /chat/markMessageAsRead/{instance}`) queda fuera
de este spec por una razón concreta: necesita el `provider_message_id` del mensaje **entrante**
que se está respondiendo, y `ChannelProvider.send()` solo recibe el mensaje **saliente** — hacerlo
bien requeriría cambiar la firma otra vez o resolverlo en otro punto del flujo. Dado que ya es
"nice to have" (el retraso ya simula humanidad de forma efectiva), se anota como mejora futura, no
se fuerza a entrar en este spec.

---

## 4. Webhook entrante — `POST /webhooks/whatsapp/{organization_slug}`

Mismo patrón que `telegram_webhook.py` (spec 007): siempre 200 salvo secreto inválido, cualquier
fallo de procesamiento se loguea y se absorbe, nunca se delega el reintento a Evolution API.

`app/api/dto/whatsapp.py` (nuevo) — **modelo tentativo**: la documentación de configuración de
webhooks confirma el evento `MESSAGES_UPSERT` para mensajes entrantes, pero no publicó un ejemplo
de payload. Se modela con los campos razonablemente esperables de un wrapper sobre el protocolo de
WhatsApp Web, y **se ajusta contra un payload real capturado en implementación** — mismo criterio
que ya usa `TelegramUpdate` (`extra="ignore"`, solo lo que el MVP necesita):

```python
class WhatsAppMessageKey(BaseModel):
    model_config = {"extra": "ignore"}
    remoteJid: str
    id: str
    fromMe: bool


class WhatsAppMessageContent(BaseModel):
    model_config = {"extra": "ignore"}
    conversation: str | None = None  # texto plano, cuando content_type es texto


class WhatsAppMessageData(BaseModel):
    model_config = {"extra": "ignore"}
    key: WhatsAppMessageKey
    message: WhatsAppMessageContent
    pushName: str | None = None
    messageTimestamp: int


class WhatsAppWebhookEvent(BaseModel):
    model_config = {"extra": "ignore"}
    event: str
    data: WhatsAppMessageData
```

`app/api/routers/whatsapp_webhook.py`:

```python
router = APIRouter(prefix="/webhooks/whatsapp", tags=["whatsapp"])


@router.post("/{organization_slug}", dependencies=[Depends(verify_whatsapp_secret)])
async def receive_whatsapp_event(
    organization_slug: str,
    payload: dict[str, Any],
    use_case: ReceiveIncomingMessageUseCase = Depends(get_receive_incoming_message_use_case),
) -> Response:
    try:
        event = WhatsAppWebhookEvent.model_validate(payload)
    except ValidationError:
        logger.warning("whatsapp.webhook.malformed_payload", organization_slug=organization_slug)
        return Response(status_code=200)

    if event.event != "MESSAGES_UPSERT" or event.data.key.fromMe:
        # fromMe=True es un mensaje que salió de este mismo número (ej. enviado manualmente desde
        # el teléfono vinculado) -- no es un mensaje del cliente, se ignora en silencio.
        return Response(status_code=200)

    if event.data.message.conversation is None:
        # multimedia -- content_type distinto de texto. Se guarda como placeholder (misma
        # decisión que spec 012 para adjuntos entrantes: mostrar el tipo, no el contenido).
        content, content_type = "[multimedia]", MessageContentType.IMAGE  # simplificado, ver nota
    else:
        content, content_type = event.data.message.conversation, MessageContentType.TEXT

    try:
        await use_case.execute(IncomingMessageInput(
            organization_slug=organization_slug,
            channel_type=ChannelType.WHATSAPP,
            external_contact_id=event.data.key.remoteJid,
            contact_display_name=event.data.pushName or event.data.key.remoteJid,
            content=content,
            content_type=content_type,
            provider_message_id=event.data.key.id,
        ))
    except Exception:
        logger.exception("whatsapp.webhook.processing_failed", organization_slug=organization_slug)

    return Response(status_code=200)
```

**Distinguir el tipo real de adjunto** (imagen vs. video vs. documento vs. audio) necesita el
payload real de Evolution API para saber en qué campo viaja esa información — se resuelve en
implementación contra un mensaje multimedia real, no se adivina aquí.

`app/security.py` — `verify_whatsapp_secret`, mismo propósito que `verify_telegram_secret` pero
**mecanismo distinto, y también pendiente de confirmar**: Telegram manda su secreto en un header
propio (`X-Telegram-Bot-Api-Secret-Token`, spec 007) porque la API de Telegram lo soporta
nativamente. La documentación de configuración de webhooks de Evolution API sí acepta un objeto
`headers` al registrar el webhook (sección 5) — razonablemente pensado para que Evolution API
reenvíe esos headers en cada llamada, pero **la documentación no lo confirma explícitamente**.
Diseño con verificación en dos niveles, para no depender solo de la parte no confirmada:

```python
async def verify_whatsapp_secret(
    x_webhook_secret: str = Header(default=""),
    organization_slug: str = Path(),
) -> None:
    if x_webhook_secret != settings.whatsapp_webhook_secret:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")
```

Si en implementación se confirma que Evolution API **no** reenvía headers personalizados, el plan
B (sin volver a este spec) es mover el secreto a la URL registrada
(`/webhooks/whatsapp/{organization_slug}/{secret}`) — el router y el caso de uso no cambian, solo
la dependencia de verificación.

---

## 5. Aprovisionamiento — script, no UI (igual que Telegram en su momento)

`scripts/register_whatsapp_instance.py` (nuevo, mismo espíritu que
`register_telegram_webhook.py`) — crea la instancia en Evolution API y registra el webhook en la
misma llamada (la documentación confirma que `POST /instance/create` acepta un objeto `webhook`
en el mismo body), e imprime el código QR en base64 para escanear:

```python
async def register_whatsapp_instance(instance_name: str, webhook_url: str, secret: str) -> None:
    async with httpx.AsyncClient(
        base_url=settings.evolution_api_base_url,
        headers={"apikey": settings.evolution_api_key},
    ) as client:
        response = await client.post(
            "/instance/create",
            json={
                "instanceName": instance_name,
                "qrcode": True,
                "webhook": {
                    "enabled": True,
                    "url": webhook_url,
                    "events": ["MESSAGES_UPSERT"],
                    "headers": {"X-Webhook-Secret": secret},
                },
            },
        )
        response.raise_for_status()
        data = response.json()

    print("Instancia creada:", data["instance"]["instanceName"])
    print("Escanea este código QR con el WhatsApp de +57 301 509 2386:")
    print(f"data:image/png;base64,{data['qrcode']['base64'][:40]}... (guardar y abrir en navegador)")
```

Guardar el `base64` completo en un archivo `.png` y abrirlo es más simple que renderizar un QR en
terminal — el script solo necesita correrse una vez por número, no es una herramienta de uso
diario.

**Mantener la sesión activa** (pedido explícito: "evitar escanear o reconectar constantemente"):
no es algo que este script controle — una vez vinculado, Evolution API mantiene la sesión
mientras el proceso siga corriendo; `WhatsAppChannelProvider.health()` (sección 3) es cómo se
detecta si se cayó. Reconectar (mostrar el QR de nuevo) solo cuando `health()` reporte `False` —
la UI para eso es spec 017, este script cubre el primer aprovisionamiento.

---

## 6. Configuración

`app/config.py` — cuatro campos nuevos, mismo patrón que los de Telegram:

```python
evolution_api_base_url: str = ""
evolution_api_key: str = ""
evolution_instance_name: str = ""
whatsapp_webhook_secret: str = ""
```

`app/dependencies.py` — el único cambio que spec 015 prometía que bastaría:

```python
@lru_cache
def get_channel_provider_registry() -> ChannelProviderRegistry:
    return ChannelProviderRegistry({
        ChannelType.TELEGRAM: TelegramChannelProvider(bot_token=settings.telegram_bot_token),
        ChannelType.WHATSAPP: WhatsAppChannelProvider(
            base_url=settings.evolution_api_base_url,
            api_key=settings.evolution_api_key,
            instance_name=settings.evolution_instance_name,
        ),
    })
```

`app/lifecycle.py` — arranca y detiene el worker de la sección 3 (el único proveedor que lo
necesita; iterar el registro y llamar `start()`/`stop()` solo en los que lo definan evita que
`ChannelProvider` tenga que declarar esos métodos para Telegram, que no los necesita):

```python
@app.on_event("startup")
async def on_startup() -> None:
    registry = get_channel_provider_registry()
    whatsapp_provider = registry.get(ChannelType.WHATSAPP)
    if isinstance(whatsapp_provider, WhatsAppChannelProvider):
        whatsapp_provider.start()
    logger.info("application.started")


@app.on_event("shutdown")
async def on_shutdown() -> None:
    registry = get_channel_provider_registry()
    whatsapp_provider = registry.get(ChannelType.WHATSAPP)
    if isinstance(whatsapp_provider, WhatsAppChannelProvider):
        await whatsapp_provider.stop()
    logger.info("application.stopped")
```

`docs/ops/whatsapp_setup.md` (nuevo) — cómo desplegar Evolution API en sí (referencia directa a
`https://docs.evolutionfoundation.com.br/en/evolution-api/install/nginx`, no se duplica esa guía
aquí), cómo correr `register_whatsapp_instance.py`, y cómo verificar `/health/ready` (spec
015 ya lo generalizó — al agregar WhatsApp al registro, la respuesta gana la clave `whatsapp` sin
tocar `health.py` otra vez).

---

## 7. Tests

Política vigente desde spec 008: este spec incluye pruebas de lo que introduce.

- `tests/test_whatsapp_provider.py` (nuevo):
  1. `send()` con `message.sender_role=ASSISTANT, is_first_reply=True` encola con
     `typing_delay_seconds == 30.0`.
  2. `send()` con `sender_role=ASSISTANT, is_first_reply=False` encola con un valor en `[2, 15]`.
  3. `send()` con `sender_role=ADVISOR` encola con `typing_delay_seconds == 0`, sin importar
     `is_first_reply`.
  4. El worker respeta la separación mínima entre dos envíos consecutivos (mockear
     `asyncio.sleep`/`time.monotonic` para no esperar segundos reales en el test).
  5. `health()` devuelve `True` solo si `state == "open"`; `False` en cualquier otro estado o si
     la llamada HTTP falla.
- `tests/test_whatsapp_webhook.py` (nuevo): payload válido de texto → `ReceiveIncomingMessageUseCase`
  invocado con `channel_type=ChannelType.WHATSAPP`; `fromMe=true` → ignorado (200, sin invocar el
  caso de uso); payload malformado → 200, sin excepción; secreto inválido → 401.
- Regresión: `ReceiveIncomingMessageUseCase` con un fake `ChannelProviderRegistry` de una entrada
  Telegram — confirmar que sigue llamando `send()` sin `is_first_reply` rompiendo nada (default
  `False`, Telegram lo ignora).

---

## Próximo paso

Spec 017 — **Admin Panel**: edición del prompt principal del agente y sus reglas de
escalamiento, número de Telegram/WhatsApp en uso, y la pantalla de conexión/QR de WhatsApp que
este spec dejó explícitamente fuera (usando `WhatsAppChannelProvider.health()` para saber cuándo
mostrarla, ver sección 5).
