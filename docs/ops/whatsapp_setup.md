# Conectar WhatsApp (Evolution API)

Guía operativa, no una spec — el diseño está en `specifications/MVP/016_WhatsApp_Integration.md`.
Cubre cómo dejar corriendo Evolution API, aprovisionar la instancia de
+57 301 509 2386, y verificar que el canal quedó activo.

**Actualizado 2026-08-22, tras la investigación y resolución del error 463** (ver
`docs/ops/whatsapp_evolution_maintenance.md` para el detalle completo de por qué se llegó a esta
configuración) — varias cosas cambiaron respecto a la versión original de este documento.

---

## 1. Levantar Evolution API

Evolution API corre como dos servicios más de `docker-compose.yml`: `evolution-api` (ya **no** la
imagen oficial de Docker Hub — se construye desde el código vendorizado en
`docker/evolution/evolution-api-fix-2608/source/`, que trae el fix del error 463 + Baileys
`7.0.0-rc13`, ver el `README.md` de esa carpeta para el porqué) y `evolution-postgres` (un
Postgres mínimo dedicado solo a esta instancia) — no hace falta instalar nada por fuera de este
repo, `docker compose build` compila la imagen la primera vez.

**Nota real, contradice la doc oficial:** "Database"/"Redis"
(https://docs.evolutionfoundation.com.br/evolution-api/requirements/) dicen que Postgres es
opcional vía `DATABASE_ENABLED=false`. Confirmado en vivo que **no es así** — el contenedor corre
migraciones de Prisma contra Postgres al arrancar sin importar `DATABASE_ENABLED`, y sin un
Postgres real alcanzable queda en bucle de reinicio (`Error: P1001: Can't reach database
server`). De ahí `evolution-postgres` en el compose — Redis sí resultó innecesario en la práctica
(`CACHE_LOCAL_ENABLED=true` funciona bien sin él).

Requiere `EVOLUTION_API_KEY`/`EVOLUTION_SERVER_URL`/`EVOLUTION_OPERATOR_EMAIL` ya presentes en
`.env` (paso 2) antes de levantarlo:

```bash
docker compose build evolution-api   # solo la primera vez, o si el código vendorizado cambió
docker compose up -d evolution-postgres evolution-api
docker logs amza-commercial-ai-platform-evolution-api-1   # confirmar que arrancó sin errores
curl http://localhost:8080   # debe responder {"status":200,"message":"Welcome to the Evolution API..."}
```

**Activación de licencia (obligatoria desde Evolution API 2.4.0, gratuita):** si los logs
muestran `License Registration Required` y las llamadas a la API responden `503
LICENSE_REQUIRED`, falta activar. Con `EVOLUTION_OPERATOR_EMAIL` ya configurado en `.env`, esto
debería resolverse solo al arrancar (log esperado: `License found`/`License activated
successfully`, o si es la primera vez con ese email, `Global API key accepted — license saved
and activated`). Si el email nunca se activó antes, la primera vez puede pedir un paso manual por
navegador — ver `docs/ops/whatsapp_evolution_maintenance.md` sección de mantenimiento futuro.

En **desarrollo local** (backend corriendo nativo, no en Docker), Evolution API queda
accesible en `http://localhost:8080` gracias al mapeo de puertos del servicio. En producción,
este servicio necesita quedar detrás de HTTPS igual que el backend (ver
https://docs.evolutionfoundation.com.br/evolution-api/install/nginx para el proxy inverso) —
`EVOLUTION_API_BASE_URL`/`EVOLUTION_SERVER_URL` deben apuntar a esa URL pública, no a
`localhost`, en ese caso.

---

## 2. Variables de entorno

En `.env` (raíz del repo, mismo archivo que ya tiene `TELEGRAM_BOT_TOKEN` etc.) — ver
`.env.example` para el detalle de cada una:

```
EVOLUTION_API_BASE_URL=http://localhost:8080
EVOLUTION_API_KEY=<elige cualquier string aleatorio largo -- es también AUTHENTICATION_API_KEY del contenedor>
EVOLUTION_INSTANCE_NAME=amza-empaques
EVOLUTION_SERVER_URL=http://localhost:8080
WHATSAPP_WEBHOOK_SECRET=<cualquier string aleatorio largo>
EVOLUTION_OPERATOR_EMAIL=<tu email -- activa la licencia gratuita de Evolution API>
```

`EVOLUTION_API_KEY` lo elige quien despliega (no es algo que Evolution API entregue) — el mismo
valor lo usan tanto este backend (para autenticar sus llamadas) como el propio contenedor (vía
`AUTHENTICATION_API_KEY` en `docker-compose.yml`, ya cableado a esta misma variable).
`WHATSAPP_WEBHOOK_SECRET` es propio de esta plataforma (lo generas tú, igual que
`TELEGRAM_WEBHOOK_SECRET`), no algo que te dé Evolution API. `EVOLUTION_OPERATOR_EMAIL` sí es de
Evolution Foundation — un email real que activa la licencia (gratis, obligatoria desde su versión
2.4.0), ver sección 1.

**En desarrollo local con ngrok:** una vez tengas `ngrok http 8000` corriendo (paso 3), actualiza
`EVOLUTION_SERVER_URL` a esa URL pública y reinicia el contenedor
(`docker compose restart evolution-api`) antes de aprovisionar la instancia — si no, Evolution
API construye sus propias respuestas/callbacks con una URL que nadie de afuera puede alcanzar.

---

## 3. Aprovisionar la instancia — SOLO la primera vez (instancia nueva)

**Importante, confirmado en vivo el 22 de agosto:** `register_whatsapp_instance.py` **NO es
idempotente**. Si la instancia (`amza-empaques`) ya existe, `POST /instance/create` responde
`403 "This name ... is already in use."` — no la recrea, no actualiza nada, simplemente falla.
Usar este script solo para crear la instancia desde cero (primera vez en un entorno nuevo, o
después de borrarla explícitamente). Para reconectar una instancia que ya existe pero perdió la
sesión (lo normal — ver sección 4), usar `/admin`, nunca este script.

Con el backend corriendo (o al menos con `.env` cargado, el script no necesita el servidor
levantado) y una URL pública donde este backend vaya a recibir el webhook (igual que Telegram —
`ngrok http 8000` en desarrollo, un dominio real en producción):

```bash
cd backend
python scripts/register_whatsapp_instance.py https://TU-URL-PUBLICA
```

Esto crea la instancia en Evolution API, registra `MESSAGES_UPSERT` apuntando a
`https://TU-URL-PUBLICA/webhooks/whatsapp/amza-empaques`, y guarda el código QR en
`backend/scripts/whatsapp_qr.png`. Ábrelo con cualquier visor de imágenes y escanéalo con el
WhatsApp de **+57 301 509 2386** (Ajustes → Dispositivos vinculados → Vincular dispositivo).

**Si la URL pública cambia** (ngrok en el plan free cambia en cada reinicio) y la instancia ya
existe, no se puede simplemente volver a correr este script — hay que actualizar el webhook por
separado: `POST /webhook/set/amza-empaques` con el body
`{"webhook": {"enabled": true, "url": "https://NUEVA-URL/webhooks/whatsapp/amza-empaques", "events": ["MESSAGES_UPSERT"], "headers": {"X-Webhook-Secret": "<WHATSAPP_WEBHOOK_SECRET>"}}}`
contra `http://localhost:8080`, con el header `apikey: <EVOLUTION_API_KEY>`.

---

## 4. Reconectar una sesión existente (lo normal, no un error)

Las sesiones de Baileys son inherentemente frágiles — se caen solas de tanto en tanto (timeouts
de WhatsApp, código 408; o un `device_removed`, código 401, si se vincula el mismo número en otro
lado). **Esto es esperado, no un bug.** Para reconectar:

1. Entrar a la app real como administrador → `/admin` → pestaña **Canales**.
2. Si dice "Desconectado", clic en **Conectar** — genera un QR nuevo ahí mismo.
3. Escanear con el WhatsApp de +57 301 509 2386.

No hace falta el script, ni tocar el webhook (sigue registrado desde el aprovisionamiento
inicial) — solo la sesión de WhatsApp se perdió, la instancia y su configuración siguen intactas.

---

## 5. Verificar que quedó conectado

```bash
curl http://localhost:8000/health/ready
```

Debe incluir `"whatsapp": true` junto a `database`/`openrouter`/`telegram` (spec 015 ya
generalizó este endpoint para iterar todo lo que esté registrado — agregar WhatsApp no tocó
`health.py`). Si sale `false`, la sesión se cayó — repetir la sección 4 para volver a mostrar el
QR desde `/admin`.

---

## 6. Probar el flujo completo

Envía un mensaje de WhatsApp real al +57 301 509 2386 desde otro número. Deberías ver, en este
orden:

1. El mensaje entrante procesado (revisar logs del backend, o `inspect_conversations.sql`).
2. Una respuesta de la IA llegando **con un retraso deliberado** (30s si es la primera respuesta
   de la conversación, 2-15s aleatorios después) — es el ritmo anti-baneo de spec 016, no un
   error ni lentitud del sistema.
3. La conversación visible en el Advisor Workspace, con `channel_type = whatsapp` (mismo chip
   que ya distingue Telegram/WhatsApp desde spec 012).

Si un asesor humano toma la conversación y responde desde el Advisor Workspace, esa respuesta
sale **sin** el retraso simulado — el retraso solo aplica a las respuestas automáticas de la IA,
un humano que decidió responder ya es el comportamiento que se busca simular.
