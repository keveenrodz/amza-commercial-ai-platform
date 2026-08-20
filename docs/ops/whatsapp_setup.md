# Conectar WhatsApp (Evolution API)

Guía operativa, no una spec — el diseño está en `specifications/MVP/016_WhatsApp_Integration.md`.
Cubre cómo dejar corriendo Evolution API, aprovisionar la instancia de
+57 301 509 2386, y verificar que el canal quedó activo.

---

## 1. Desplegar Evolution API

Evolution API es un servicio aparte (self-hosted), no algo que corra dentro de este repo. Seguir
la guía oficial, no se duplica aquí porque cambia con cada versión de Evolution API:

- https://docs.evolutionfoundation.com.br/en/evolution-api/install/nginx (instalación + nginx
  como proxy inverso — necesario porque Evolution API necesita ser accesible por HTTPS desde
  fuera, igual que este backend necesita serlo para recibir webhooks)

Al terminar tendrás una URL base (ej. `https://evolution.tu-dominio.com`) y una API key —
guárdalas para el paso 3.

---

## 2. Variables de entorno

En `.env` (raíz del repo, mismo archivo que ya tiene `TELEGRAM_BOT_TOKEN` etc.):

```
EVOLUTION_API_BASE_URL=https://evolution.tu-dominio.com
EVOLUTION_API_KEY=<api key de tu despliegue de Evolution API>
EVOLUTION_INSTANCE_NAME=amza-empaques
WHATSAPP_WEBHOOK_SECRET=<cualquier string aleatorio largo>
```

`WHATSAPP_WEBHOOK_SECRET` es propio de esta plataforma (lo generas tú, igual que
`TELEGRAM_WEBHOOK_SECRET`), no algo que te dé Evolution API.

---

## 3. Aprovisionar la instancia (crea + registra webhook + genera QR)

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

**Nota:** igual que con `register_telegram_webhook.py`, si la URL pública cambia (ngrok en el
plan free cambia en cada reinicio) hay que volver a correr este script — sí vuelve a crear la
instancia si ya existe, Evolution API lo maneja de forma idempotente.

---

## 4. Verificar que quedó conectado

```bash
curl http://localhost:8000/health/ready
```

Debe incluir `"whatsapp": true` junto a `database`/`openrouter`/`telegram` (spec 015 ya
generalizó este endpoint para iterar todo lo que esté registrado — agregar WhatsApp no tocó
`health.py`). Si sale `false`, la sesión se cayó — repetir el paso 3 para volver a mostrar el QR.

**Mantener la sesión activa** no es algo que este script controle: una vez vinculado, Evolution
API mantiene la sesión mientras su propio proceso siga corriendo. `WhatsAppChannelProvider.health()`
es la forma de detectar si se cayó (ver arriba); reconectar (mostrar el QR de nuevo) desde
`/admin` es spec 017, no este documento.

---

## 5. Probar el flujo completo

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
