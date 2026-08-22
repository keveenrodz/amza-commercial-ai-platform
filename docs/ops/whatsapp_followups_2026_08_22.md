# Seguimientos de WhatsApp/Telegram — post error 463 (22 de agosto)

Después de cerrar la investigación del error 463 (ver `docs/ops/whatsapp_evolution_maintenance.md`),
el usuario pidió en un solo mensaje una lista larga de mejoras/bugs/preguntas sobre el
comportamiento real de WhatsApp/Telegram. Este documento es el estado de esa lista — se armó
porque la sesión se cortó a mitad de camino (batería baja del usuario) y no debe perderse nada.

**Prioridad que el usuario dio, en orden:** 1) contacto duplicado LID/teléfono, 2) notificación
de desconexión + contador de QR, 3) mensajes enviados desde WhatsApp nativo, 4) concurrencia/cola
de mensajes.

---

## Ítem 1 — Contacto duplicado por LID vs. número de teléfono — ✅ COMPLETO

**Síntoma reportado:** un mismo cliente real (+573217227941, "Matamed", luego renombrado a
"Kevs - Matamed" en WhatsApp) aparecía como dos conversaciones distintas.

**Causa raíz real (no era el cambio de nombre):** WhatsApp está migrando a un identificador
"LID". El mismo contacto llega unas veces como `remoteJid="<lid>@lid"` y otras como
`"<numero>@s.whatsapp.net"`. Nuestro webhook usaba `remoteJid` tal cual como identidad del
contacto, sin capturar ni usar `remoteJidAlt` (el JID de número real que Evolution API manda
junto a un mensaje en formato LID).

**Implementado** (commit `2e59dce`):
- `backend/app/api/dto/whatsapp.py`: `WhatsAppMessageKey` ahora captura `remoteJidAlt` y expone
  `canonical_jid` (propiedad), que prefiere el JID de número real sobre el LID cuando está
  disponible.
- `backend/app/api/routers/whatsapp_webhook.py`: usa `event.data.key.canonical_jid` en vez de
  `remoteJid` directo, tanto para `external_contact_id` como para el fallback del nombre.
- `backend/app/use_cases/receive_incoming_message.py`: además, si el contacto ya existe pero
  `display_name` cambió, se actualiza (antes se quedaba con el nombre de la primera vez para
  siempre — bug relacionado, encontrado en el mismo pase).
- Datos reales: se fusionó a mano el par duplicado ya existente (contacto `d432a294...` +
  `64f97ae9...`) en una sola conversación con 10 mensajes en orden cronológico.
- Tests nuevos en `test_whatsapp_webhook.py` (normalización LID→número, y fallback sin
  `remoteJidAlt`) y `test_contact_enrichment.py` (actualización de `display_name`).

**Nada pendiente en este ítem.**

---

## Ítem 2 — Notificación de desconexión + contador de QR — ✅ COMPLETO

**Diseño acordado con el usuario:** un chequeo periódico cada 60s, pero el usuario preguntó
explícitamente si eso afectaría el sistema — se confirmó que `/health/ready` hace llamadas
externas reales (OpenRouter, Evolution API, Telegram) cada vez que se consulta, así que si cada
pestaña de cada asesor lo consultara cada 60s, sí sumaría tráfico externo innecesario. Se resolvió
con una arquitectura de una sola revisión real por intervalo, sin importar cuántas pestañas estén
abiertas.

**Implementado** (commit `1edc777`):
- `backend/app/services/channel_health_monitor.py` (nuevo): `ChannelHealthMonitor`, un worker en
  segundo plano (mismo patrón que el worker de WhatsApp de spec 016) que revisa la salud real
  cada 60s y cachea el resultado en memoria (`self._status`). Arrancado/detenido en
  `app/lifecycle.py`, junto al worker de WhatsApp.
- `backend/infrastructure/channels/telegram.py`: nuevo método `webhook_health()` — a diferencia
  de `health()` (que solo confirma que el token del bot es válido), consulta `getWebhookInfo` de
  Telegram para detectar el caso real: la URL pública registrada (ngrok en desarrollo) rotó y
  nadie volvió a registrar el webhook. Revisa que haya una `url` registrada y que no haya
  `last_error_date` reciente.
- `backend/app/api/routers/health.py`: nuevo `GET /health/status` — lee el caché del monitor,
  **nunca** llama a los providers reales. Este es el que consulta el frontend, no `/health/ready`.
- `backend/app/dependencies.py`: `get_channel_health_monitor()` (singleton `@lru_cache`, mismo
  patrón que el resto del archivo).
- `frontend/hooks/use-channel-health.ts` (nuevo): `useChannelHealth()`, sondea
  `/api/health/status` cada 60s (`refetchInterval`).
- `frontend/components/channel-disconnect-toast.tsx` (nuevo): popup traslúcido, esquina
  inferior derecha, uno por canal caído, con botón de cerrar. Solo vuelve a notificar si el canal
  se recuperó y se cayó de nuevo (no se repite en cada sondeo mientras sigue caído). Mensaje
  distinto para WhatsApp (con link "Ir a Canales →") vs. Telegram (pide revisar el webhook, sin
  botón de acción porque no hay nada que hacer desde la UI).
- Montado en `frontend/components/workspace-shell.tsx` — visible desde cualquier pantalla del
  workspace, no solo `/admin`.
- `frontend/app/(workspace)/admin/page.tsx` (`WhatsAppChannelCard`): el QR ahora muestra un
  contador circular en la esquina inferior derecha de la imagen, empezando en 45 segundos
  (confirmado en el código real de Evolution API: `qrTimeout: 45_000` en
  `docker/evolution/evolution-api-fix-2608/source/src/api/integrations/channel/whatsapp/whatsapp.baileys.service.ts`).
  Al llegar a 0, pide un QR nuevo automáticamente (antes se quedaba una imagen ya inválida en
  pantalla sin ningún aviso).

**Bug real encontrado y corregido durante la verificación en vivo (antes de este commit, no
después):** el efecto del toast mutaba una ref (`notifiedRef`) *dentro* de un updater funcional
de `setState`. React 18 Strict Mode (activo por defecto en `next dev`) invoca los updaters
funcionales dos veces para detectar impurezas — la segunda invocación ya encontraba la ref
mutada y descartaba la actualización, dejando el toast sin mostrarse nunca en desarrollo. Se
corrigió moviendo la mutación de la ref fuera del updater, al cuerpo del efecto. Verificado de
nuevo tras el fix: `tsc`/`eslint` limpios (no se volvió a correr Playwright después del fix por
la urgencia de guardar el estado — **recomendado hacerlo al retomar**, aunque el razonamiento del
fix es sólido y el mismo patrón ya se usa en otras partes del código sin problema).

**Verificado visualmente con Playwright, sin tocar la sesión real de WhatsApp** (se interceptaron
las llamadas de red y se sirvieron respuestas simuladas): el contador del QR funciona
correctamente (arranca en 45, cuenta hacia abajo). El toast, una vez corregido el bug de Strict
Mode, no se volvió a verificar visualmente con el código ya arreglado — pendiente de una pasada
rápida de confirmación, no crítico dado que la causa y el fix son claros.

**Nada más pendiente en este ítem**, salvo la reconfirmación visual opcional mencionada arriba.

---

## Ítem 3 — Mensajes enviados desde WhatsApp nativo no se reflejan — ❌ NO INICIADO

**Confirmado (solo investigación, nada implementado):** `backend/app/api/routers/whatsapp_webhook.py`
línea ~38 descarta explícitamente todo evento con `fromMe: true`. Si un asesor responde
directamente desde su WhatsApp (móvil o web), ese mensaje nunca se guarda ni se muestra en la
app.

**Plan ya pensado, no ejecutado:**
1. Cuando llegue `fromMe: true`, no ignorarlo sin más — pero cuidado: nuestros propios envíos
   (vía `WhatsAppChannelProvider._send_now()`) **también** generan un evento `messages.upsert`
   con `fromMe: true` en el webhook (Baileys reporta sus propios envíos salientes igual). Sin
   distinguir, se procesaría un mensaje que ya guardamos nosotros mismos como si fuera nuevo.
2. La deduplicación por `provider_message_id` que ya se implementó hoy (commit `0540526`,
   ítem del "pendiente de endurecer" que abrió esta sesión) es justo la pieza que permite hacer
   esto de forma segura: si un `fromMe:true` trae un `provider_message_id` que ya existe en
   nuestra base (porque lo mandamos nosotros), se ignora; si no existe, es un mensaje genuino
   enviado por el humano desde su WhatsApp nativo — hay que guardarlo con
   `sender_role=ADVISOR` (o similar) y **sin** disparar una respuesta de IA.
3. Falta decidir: ¿a qué advisor_id se le atribuye ese mensaje? WhatsApp no dice qué humano
   específico lo mandó si hay varias personas con acceso al mismo teléfono/WhatsApp Web. Posible
   respuesta: no atribuir a nadie específico (mostrar como "Asesor" genérico, como ya hace la UI
   para mensajes sin nombre — ver `frontend/components/chat-bubble.tsx::bubbleLabel()`), o
   atribuir al `assigned_advisor_id` de la oportunidad si existe.
4. También hay que decidir: si el humano responde desde WhatsApp nativo, ¿debe eso cambiar
   `attention_mode` de la oportunidad (de IA a humano), igual que responder desde la app ya lo
   hace? Probablemente sí, por consistencia — pero no se confirmó con el usuario.

**Siguiente paso al retomar:** proponer el diseño exacto (con las dos decisiones de arriba) al
usuario antes de escribir código, no asumir.

---

## Ítem 4 — Concurrencia de 30-50 clientes simultáneos — ❌ NO INICIADO (hallazgo urgente)

**Confirmado por lectura de código, no implementado ningún cambio:**
`backend/infrastructure/channels/whatsapp.py::WhatsAppChannelProvider` tiene **una sola
`asyncio.Queue` y un solo `_run_worker()`**, compartida por todas las conversaciones (es un
singleton vía `@lru_cache`). Los envíos se procesan uno por uno, en fila estricta (FIFO).

**El problema real:** si 30 personas escriben por primera vez al mismo tiempo, cada una debería
esperar 30s (el delay de la primera respuesta, `_FIRST_REPLY_DELAY`) — pero como el worker es
serial, el mensaje #30 en la fila no sale a los 30s sino a los ~15 minutos (30 × 30s), porque
tiene que esperar a que el worker termine de procesar y enviar los 29 anteriores primero.

**No se ha diseñado la solución todavía.** Opciones a evaluar con el usuario (ninguna decidida):
- Un worker/cola **por conversación** en vez de uno global — permite que 30 conversaciones
  avancen en paralelo, cada una con su propio ritmo de 30s/2-15s. Riesgo: enviar a 30 destinatarios
  distintos casi simultáneamente podría en sí mismo parecer sospechoso para la detección
  anti-spam de WhatsApp (no confirmado, es una hipótesis razonable dado todo lo aprendido en la
  investigación del 463 sobre patrones de envío).
- Un límite de concurrencia intermedio (ej. N workers en paralelo, no 1 ni 30) — un punto medio
  entre "todo en fila" y "todo en paralelo".
- Mantener una sola cola pero re-priorizar: procesar "primera respuesta" antes que respuestas de
  seguimiento, para que al menos los contactos nuevos no se acumulen detrás de conversaciones ya
  en curso.

**Siguiente paso al retomar:** esto es más una decisión de arquitectura/producto (cuánto riesgo
de baneo aceptar a cambio de mejor tiempo de respuesta bajo volumen) que una implementación
directa — presentar las opciones al usuario antes de tocar código.

---

## Otros hallazgos de la investigación inicial (no priorizados explícitamente, quedan documentados)

Estos surgieron de las preguntas originales del usuario pero no están en su lista de 4
prioridades — no se han implementado, quedan aquí para no perderlos:

- **Etiquetas de WhatsApp (labels):** Evolution API sí las soporta de verdad (endpoint
  `GET /label/findLabels`, tabla `Label`, eventos de webhook `labels.edit`/`labels.association`).
  **Solo funciona si el número conectado es una cuenta WhatsApp Business** — si es WhatsApp
  normal, esos eventos nunca se disparan. No confirmado si +57 301 509 2386 es cuenta Business.
- **Catálogo de datos de cliente disponibles vía Evolution API** (para marketing/analítica):
  nombre, foto de perfil (siempre); bajo demanda (`POST /chat/fetchProfile`): estado/"about",
  si es cuenta Business, email, descripción, sitio web; si es Business
  (`POST /chat/fetchBusinessProfile`): categoría de negocio, dirección; presencia en tiempo real
  (en línea/escribiendo/última vez) vía webhook si nos suscribimos primero. No se guarda
  `verifiedBizName`. Nada de esto se está usando actualmente, es solo lo que existe disponible.
- **`phone_number` del Contact siempre es `null`, para WhatsApp y Telegram por igual** — problema
  cosmético confirmado (muestra "—" en el panel de contacto), no es el bug del panel vacío que
  reportó el usuario (ver abajo). Se podría derivar de `external_id` para WhatsApp fácilmente si
  se decide arreglarlo.
- **Panel de contacto "no muestra nada" al hacer clic:** se intentó reproducir en vivo con
  Playwright, probando las 3 conversaciones reales de WhatsApp y 2 de Telegram, ambos roles, dos
  formas de navegación — **no se pudo reproducir**, el panel abrió correctamente con todos los
  datos en todos los casos. Hipótesis: caché/estado obsoleto del servidor de desarrollo (se
  reinició muchas veces ese día). **Si vuelve a pasar:** pedir al usuario que abra la consola del
  navegador antes de hacer clic, para capturar el error real en el momento.
- **Ritmo de mensajes automáticos (confirmado, no requiere cambios salvo que se decida lo
  contrario):** 30s fijos solo en la primera respuesta de una conversación, 2-15s aleatorios en
  cada respuesta siguiente, más una pausa mínima aleatoria de 2-5s entre cualquier par de envíos
  consecutivos (sin importar la conversación) — todo en
  `backend/infrastructure/channels/whatsapp.py`.
- **Dos temas que el usuario marcó explícitamente como "para discutir", no para implementar
  todavía:**
  1. El mensaje de la IA se guarda y se muestra en la app (con su timestamp) en el momento en que
     se genera, no cuando realmente sale por WhatsApp (hasta 30s después, por el delay
     anti-baneo) — confuso para el asesor humano viendo la conversación en tiempo real.
  2. "Escribiendo..." aparece apenas llega el mensaje del cliente, pero la respuesta real tarda
     hasta 30s — sensación de espera incómoda. El usuario entiende que es por la política
     anti-baneo y pide explorar un ajuste sin sacrificarla, no eliminarla.
  Ninguno de los dos tiene una solución diseñada todavía — quedan para una conversación de diseño
  específica, no son bugs con un fix obvio (afectan directamente el ritmo anti-baneo que protege
  la cuenta real).

---

## Cómo retomar

1. Confirmar que el backend sigue corriendo con el código de hoy: `curl http://localhost:8000/health/status`
   debe responder `{"telegram":true,"whatsapp":true}` (si no, reiniciar `python main.py` desde
   `backend/`, normal después de cualquier corte de sesión).
2. Reconfirmar visualmente el toast de desconexión ya con el fix aplicado (opcional pero
   recomendado, ver ítem 2).
3. Diseñar y confirmar con el usuario el ítem 3 (mensajes desde WhatsApp nativo) — las dos
   decisiones pendientes están listadas arriba.
4. Presentar las opciones del ítem 4 (concurrencia) al usuario — es una decisión de
   producto/riesgo, no solo de código.
5. Los "para discutir" (timing de mensajes/typing) quedan para cuando el usuario quiera retomar
   esa conversación específica — no son parte de la lista de 4 prioridades que dio.
