# Correr y probar la plataforma completa en local

Guía operativa, no una spec — el diseño está en `specifications/MVP/006_...md` a `009_...md`.
Esto es el "cómo hacerlo" para levantar y probar todo lo construido hasta spec 009: el flujo de
Telegram (cliente → IA) y el Advisor Workspace (asesor humano → toma/devuelve conversaciones).

Requisito previo: setup base ya hecho (`README.md` — Python 3.12, Node 20, `pip install -e
".[dev]"`, `npm install`).

---

## 1. Obtener credenciales reales

Salta esta sección si tu `.env` ya tiene valores reales (`git diff .env.example .env` para
comparar). Las tres integraciones son independientes — puedes tener solo una funcionando.

### OpenRouter (IA)

1. Cuenta en https://openrouter.ai
2. https://openrouter.ai/keys → crear una API key
3. `OPENROUTER_API_KEY=sk-or-v1-...` en `.env`

Necesita saldo cargado para funcionar (ver https://openrouter.ai/credits) — sin saldo, las
llamadas devuelven error de pago, no un error de configuración.

### Telegram (canal cliente)

1. Habla con `@BotFather` en Telegram → `/newbot` → sigue las instrucciones
2. Te da un token tipo `123456789:AAE...` → `TELEGRAM_BOT_TOKEN=...` en `.env`
3. `TELEGRAM_WEBHOOK_SECRET` — cualquier string aleatorio largo, ej.
   `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`

### Google OAuth (login del asesor)

1. https://console.cloud.google.com/ → crear proyecto (o usar uno existente)
2. **APIs y servicios → Pantalla de consentimiento de OAuth**
   - Tipo de usuario: **Externo**
   - Nombre de la app, correo de soporte y de contacto — lo mínimo requerido
   - Sección "Usuarios de prueba" → agregar los emails de Google con los que vas a probar
     (mientras la app no esté publicada, **solo esos emails pueden autenticarse** — ver sección
     "Publicar la app" abajo para eliminar esta restricción)
3. **APIs y servicios → Credenciales → + Crear credenciales → ID de cliente de OAuth**
   - Tipo de aplicación: **Aplicación web**
   - URIs de redirección autorizados: `http://localhost:3000/api/auth/google/callback`
     (⚠️ apunta al **proxy del frontend** — `:3000/api/...`, nunca directo al backend `:8000` — si
     no, la cookie de sesión queda con el origen equivocado y el login no funciona en la
     práctica, aunque Google sí complete el flujo)
4. Copia el **Client ID** y **Client secret** del modal (o descarga el JSON) →
   `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` en `.env`
5. `GOOGLE_REDIRECT_URI=http://localhost:3000/api/auth/google/callback` en `.env` (debe coincidir
   carácter por carácter con lo puesto en el paso 3)

**Publicar la app (recomendado, evita repetir el paso de "usuarios de prueba" por cada persona
nueva):** en la misma pantalla de consentimiento OAuth, botón **"Publicar aplicación"**. Como
solo se piden scopes básicos (`openid email profile`), Google lo permite sin proceso de
verificación. Los usuarios verán una advertencia de "app no verificada" que pueden pasar con un
click — no bloquea nada. Detalle completo en `docs/ops/onboarding_internal_users.md`.

### JWT (sesión propia del backend)

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

`JWT_SECRET=...` en `.env`. `JWT_TTL_HOURS=24` (default, no hace falta tocarlo).

---

## 2. Sembrar datos de prueba

```bash
cd backend
conda activate amza-commercial-ai-platform
python scripts/seed_dev_data.py
```

Crea `Organization` (`amza-empaques`) + `Agent` (`openai/gpt-4.1-nano`) si no existen —
idempotente, se puede correr varias veces sin duplicar nada.

Crea también un `InternalUser` por cada persona que vaya a usar el Advisor Workspace — usa el
email exacto de una cuenta de Google real (la que agregaste como "usuario de prueba" en la
sección 1, si la app OAuth sigue sin publicar):

```bash
python scripts/create_user.py --org amza-empaques --email tu-email@gmail.com \
    --name "Tu Nombre" --role advisor
```

Detalle completo (cómo dar/quitar acceso) en `docs/ops/onboarding_internal_users.md`.

---

## 3. Arrancar los dos servidores

**Terminal 1 — backend:**

```bash
cd backend && conda activate amza-commercial-ai-platform && python main.py
```

Verificar: `curl http://localhost:8000/health/ready` → `{"database":true,"openrouter":true,"telegram":true}`
(si alguno sale `false`, revisar esa credencial específica antes de seguir).

**Terminal 2 — frontend:**

```bash
cd frontend && npm run dev
```

Requiere `frontend/.env.local` con `BACKEND_URL=http://localhost:8000` (no es el mismo archivo
que la raíz — Next.js no lee el `.env` de la raíz en desarrollo local, solo Docker Compose lo
hace). Si no existe, créalo con esa única línea.

Verificar: `curl http://localhost:3000/api/health` → mismo resultado que el backend directo —
confirma que el proxy (`next.config.ts`) está reenviando correctamente.

---

## 4. Probar el flujo de Telegram (cliente → IA)

Telegram necesita alcanzar tu máquina desde internet — en local hace falta un túnel:

```bash
ngrok http 8000
```

Copia la URL de `Forwarding` y registra el webhook (un solo comando, toma el token/secreto de
`Settings`, no hay que copiarlos a mano):

```bash
cd backend
python scripts/register_telegram_webhook.py https://TU-URL.ngrok-free.dev
```

Confirmar: `curl https://TU-URL.ngrok-free.dev/health` → `{"status":"ok"}`.

**Escríbele al bot desde Telegram** (buscar por el username exacto, confirmarlo con
`curl https://api.telegram.org/bot<TOKEN>/getMe`). Deberías recibir respuesta del agente de IA
en segundos.

Confirmar qué se guardó, sin depender de la respuesta de Telegram como única prueba:

```bash
sqlite3 backend/data/amza.db < backend/scripts/inspect_conversations.sql
```

**Nota:** cada reinicio de `ngrok` (plan free) cambia la URL — hay que repetir el
`register_telegram_webhook.py` cada vez. La URL de Google (`GOOGLE_REDIRECT_URI`) es distinta y
no depende de ngrok, porque el login pasa por tu propio navegador, no por servidores de Telegram
llamando a tu máquina.

---

## 5. Probar el Advisor Workspace (asesor humano)

Con los dos servidores corriendo (sección 3), sin necesidad de ngrok esta vez — el navegador ya
puede llegar directo a `localhost:3000`:

1. Abre `http://localhost:3000` → redirige a `/login`
2. "Iniciar sesión con Google" → completa el login con una cuenta que tenga un `InternalUser`
   creado (sección 2)
3. Termina en `/opportunities` — deberías ver las conversaciones de Telegram de la sección 4 (si
   ninguna está asignada, todas aparecen en "Sin asignar" y "Todas", "Mías" vacía)
4. Entra a una conversación → **Tomar conversación** → confirma que regresa a la lista y ahora
   aparece en "Mías"
5. Entra de nuevo a esa conversación (ya asignada a ti) → escribe un mensaje en el campo de texto
   y **Enviar** (spec 010) → confirma en Telegram, desde el lado del cliente, que el mensaje
   llega. El input se limpia solo al terminar — esa es la confirmación de que funcionó
6. Vuelve a entrar → **Devolver a IA** → confirma que regresa a "Sin asignar"
7. **Cerrar sesión** → confirma que vuelve a pedir login

Si algo no funciona como se describe arriba, es una regresión real, no un comportamiento
esperado — ver la sección de diagnóstico abajo.

---

## 6. Correr los tests automatizados

```bash
# Backend -- 9 tests, cubre login/identidad de punta a punta con un AuthProvider fake
cd backend && pytest

# Frontend e2e -- 3 tests, cubre el Advisor Workspace interceptando /api/* a nivel de navegador
# (no requiere backend ni Google reales corriendo -- arranca su propio servidor de prueba)
cd frontend && npx playwright test
```

Ninguno de los dos requiere las credenciales reales de la sección 1 — ambos usan un
`AuthProvider`/interceptor fake. Correr esto primero si algo falla en la prueba manual, para
aislar si el problema es de configuración/credenciales (fallaría solo lo manual) o de código
(fallarían también los tests).

---

## 7. Diagnóstico — problemas ya vistos, cómo reconocerlos

**Cambiaste código del backend (por ejemplo, al implementar una spec nueva) y el frontend actúa
como si esa ruta/campo no existiera (404, o el botón "no hace nada").** El backend **no recarga
solo** salvo que `DEBUG=true` en `.env` (`main.py`: `reload=settings.debug`). Si tu terminal de
`python main.py` lleva rato corriendo desde antes del cambio, sigue sirviendo el código viejo.
Confirmarlo sin adivinar:
```bash
curl -s http://localhost:8000/openapi.json | python3 -c \
  "import json,sys; print('/ruta/nueva' in json.load(sys.stdin)['paths'])"
```
Si da `False` (o la ruta ni aparece), mata ese proceso (`lsof -i :8000`, `kill <PID>`) y vuelve a
arrancar `python main.py` en su terminal. Encontrado en la validación manual de spec 010: el
proceso llevaba corriendo desde antes de implementar `POST .../messages`, así que el botón
"Enviar" no hacía nada visible (404 silencioso, sin manejo de error en la UI en ese momento).

**"Address already in use" al arrancar el backend, pero `/health` responde igual.** Hay un
proceso viejo escuchando en el puerto 8000 desde antes — tu intento nuevo falló a bindear en
silencio y el proceso viejo (con código desactualizado) sigue respondiendo. Diagnóstico:
```bash
lsof -i :8000
```
Si aparece un PID que no reconoces del arranque actual, mátalo por PID exacto (`kill -9 <PID>`,
nunca `pkill` genérico si hay ambigüedad) y vuelve a arrancar.

**El login con Google "funciona" pero `/organizations/*` sigue dando 401 después.** Revisar que
`GOOGLE_REDIRECT_URI` apunte al proxy (`:3000/api/...`), no al backend directo (`:8000/...`) — ver
sección 1. Si apunta al backend, la cookie queda con el origen equivocado y nunca viaja en las
llamadas reales del frontend, aunque el login en sí parezca completarse.

**Google devuelve "esta app no está verificada" o rechaza el login.** El email que estás usando
no está en la lista de "usuarios de prueba" de la pantalla de consentimiento OAuth (sección 1) —
o publica la app (recomendado) o agrega ese email ahí.

**El botón de una acción (login, logout, tomar, devolver) no parece hacer nada.** Antes de asumir
que el backend falló, revisar la consola del navegador (Network tab) — varias veces el problema
fue el frontend fallando a interpretar una respuesta válida del backend (ver
`project_technical_decisions.md` en la memoria del proyecto: nunca asumir que un 200 trae body
JSON). El backend respondiendo bien no garantiza que el frontend lo esté leyendo bien.

**`/auth/me` devuelve datos de otra sesión de la que crees.** Las cookies persisten entre
reinicios del navegador hasta que expiran (24h) o haces logout explícito — si cambiaste de
cuenta sin cerrar sesión primero, es esperado ver la sesión anterior.
