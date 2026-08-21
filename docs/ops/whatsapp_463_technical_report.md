# Reporte técnico: error 463 (WhatsApp) al responder a contactos — Evolution API / Baileys

**Fecha:** 2026-08-21
**Estado:** Bloqueador crítico, sin resolver. WhatsApp es el canal principal del piloto (no
Telegram), así que sin esto el flujo de atención automática a clientes nuevos no funciona.

---

## 1. Resumen del problema

- Los mensajes **entrantes** de WhatsApp funcionan perfecto (webhook recibido, contacto y
  conversación creados, respuesta de la IA generada y visible en la app).
- El envío de la respuesta (`POST /message/sendText`) es **aceptado por Evolution API (201
  Created / status inicial `PENDING`)**, pero la entrega real es **rechazada por los servidores
  de WhatsApp en silencio**, sin que la API devuelva ningún error HTTP — el rechazo llega después,
  como una actualización de estado del mensaje:

```json
{
  "key": { "remoteJid": "573217227941@s.whatsapp.net", "fromMe": true, "id": "3EB0CF7D71657E3D075BFB" },
  "update": { "status": 0, "messageStubParameters": ["463"] }
}
```

  `status: 0` = mensaje fallido (ERROR). `messageStubParameters: ["463"]` es el código de error
  interno de WhatsApp/Baileys para **`NackCallerReachoutTimelocked`**.

## 2. ¿Qué es el error 463?

Es un mecanismo anti-spam del lado de **los servidores de WhatsApp** (no de Evolution API ni de
este proyecto): antes de permitir que una cuenta le responda a un contacto, WhatsApp exige que el
cliente incluya en el mensaje saliente un token de privacidad (`tctoken`/`cstoken`) que se extrae
del mensaje **entrante** de ese contacto. Si la librería que habla el protocolo de WhatsApp Web
no extrae/persiste/reenvía correctamente ese token, WhatsApp interpreta el mensaje saliente como
un "acercamiento" (reach-out) no autorizado a un contacto "en frío" y lo bloquea con un
time-lock.

Fuentes oficiales (mantenedores de las librerías, no foros ni IA):
- [WhiskeySockets/Baileys#2441](https://github.com/WhiskeySockets/Baileys/issues/2441) —
  investigación de los propios mantenedores de Baileys, fix parcial (PRs #2257, #2339, #2438),
  sin resolución completa.
- [WhiskeySockets/Baileys#2698](https://github.com/WhiskeySockets/Baileys/issues/2698) — reporte
  de que persiste incluso en contactos "warm", ya con los parches de tctoken aplicados.
- [evolution-foundation/evolution-api#2653](https://github.com/evolution-foundation/evolution-api/issues/2653) —
  mismo síntoma exacto (`status 0`, `messageStubParameters: ["463"]`) reportado por otro usuario
  en la misma versión que usamos (v2.3.7), sin solución del mantenedor.

## 3. Puerto y configuración — ¿coincide con lo recomendado?

**Sí.** El puerto `8080` es el puerto por defecto documentado oficialmente para Evolution API
(`https://docs.evolutionfoundation.com.br/evolution-api/install/docker`). No hay ninguna
desviación de la configuración recomendada en ese sentido.

### `docker-compose.yml` (servicios relevantes, texto completo)

```yaml
evolution-postgres:
  image: postgres:15
  restart: always
  environment:
    - POSTGRES_USER=evolution
    - POSTGRES_PASSWORD=evolution
    - POSTGRES_DB=evolution_db
  volumes:
    - evolution_postgres_data:/var/lib/postgresql/data

evolution-api:
  image: evoapicloud/evolution-api:v2.3.7
  restart: always
  ports:
    - "8080:8080"
  environment:
    - AUTHENTICATION_API_KEY=${EVOLUTION_API_KEY}
    - SERVER_URL=${EVOLUTION_SERVER_URL:-http://localhost:8080}
    - DATABASE_ENABLED=true
    - DATABASE_PROVIDER=postgresql
    - DATABASE_CONNECTION_URI=postgresql://evolution:evolution@evolution-postgres:5432/evolution_db?schema=public
    - DATABASE_SAVE_DATA_INSTANCE=true
    - DATABASE_SAVE_DATA_NEW_MESSAGE=true
    - DATABASE_SAVE_MESSAGE_UPDATE=true
    - CACHE_REDIS_ENABLED=false
    - CACHE_LOCAL_ENABLED=true
  volumes:
    - evolution_instances:/evolution/instances
  depends_on:
    - evolution-postgres
```

### Variables de entorno relevantes (`.env`)

```
EVOLUTION_API_BASE_URL=http://localhost:8080
EVOLUTION_API_KEY=zpOkCrmkOdUFfoSi489cBVa1CD82bDKo9RinM-HmPyc
EVOLUTION_INSTANCE_NAME=amza-empaques
EVOLUTION_SERVER_URL=http://localhost:8080
WHATSAPP_WEBHOOK_SECRET=9FSB7uU3o7YbrgfqgyrfzmZQYCUsQRnLdfKwZJm4P_Y
```

(`EVOLUTION_API_KEY` y `WHATSAPP_WEBHOOK_SECRET` son secretos elegidos por nosotros al desplegar
— no son credenciales entregadas por Meta/WhatsApp ni por Evolution Foundation. Rotarlos si se
comparte este documento fuera de un equipo de confianza.)

### Versiones exactas

```
Evolution API: v2.3.7
Baileys WhatsApp Web version (reportado por la API): 2.3000.1045745970
Integration type de la instancia: WHATSAPP-BAILEYS
Postgres: 15
Docker Engine: 29.7.2
Host OS: Linux 6.8.0-136-generic (Ubuntu 22.04)
```

### Estado de la instancia (`GET /instance/fetchInstances`)

```json
{
  "id": "91116aa0-ffb4-4ca7-8646-cd426dd83f56",
  "name": "amza-empaques",
  "connectionStatus": "open",
  "ownerJid": "573015092386@s.whatsapp.net",
  "integration": "WHATSAPP-BAILEYS",
  "Setting": {
    "rejectCall": false, "groupsIgnore": false, "alwaysOnline": false,
    "readMessages": false, "readStatus": false, "syncFullHistory": false
  },
  "_count": { "Message": 35, "Contact": 8, "Chat": 4 }
}
```

`GET /instance/connectionState/amza-empaques` confirma en vivo: `{"instance":{"instanceName":"amza-empaques","state":"open"}}`
— la sesión está activa y estable (16+ horas de uptime continuo al momento de este reporte, sin
caídas espontáneas salvo un logout manual nuestro durante pruebas de la UI de administración).

## 4. Evidencia de logs — reproducción controlada, en vivo, para este reporte

**Request enviado** (respuesta al mismo número de prueba de ayer, ya con historial de mensajes
previo — no es un contacto nuevo):

```
POST http://localhost:8080/message/sendText/amza-empaques
{"number": "573217227941@s.whatsapp.net", "text": "Reporte tecnico - prueba controlada"}

→ HTTP 201
{"key":{"remoteJid":"573217227941@s.whatsapp.net","fromMe":true,"id":"3EB0CF7D71657E3D075BFB"},
 "status":"PENDING", ...}
```

**Log de Evolution API pocos segundos después** (mismo `id` de mensaje):

```
Update messages [
  {
    "key": {
      "remoteJid": "573217227941@s.whatsapp.net",
      "fromMe": true,
      "id": "3EB0CF7D71657E3D075BFB"
    },
    "update": { "status": 0, "messageStubParameters": ["463"] }
  }
]
```

El mensaje nunca llega al teléfono del cliente.

## 5. Qué se descartó ya, con evidencia real (no solo teoría)

| Hipótesis probada | Resultado |
|---|---|
| ¿Es una condición de carrera de caché local (vs. Redis)? | Descartado — el "truco de la reacción" (`/message/sendReaction`) enviado manualmente, con segundos de margen tras el mensaje entrante, falló con el mismo 463 instantáneo. Si fuera timing, ese margen habría bastado. |
| ¿Falta marcar como leído / mostrar "escribiendo..." antes de responder? | Probado (`/chat/markMessageAsRead` + `/chat/sendPresence`) — sin cambio en el resultado. |
| ¿Faltan flags de persistencia en BD? | Se agregaron `DATABASE_SAVE_DATA_NEW_MESSAGE`/`DATABASE_SAVE_MESSAGE_UPDATE` — sin cambio. |
| ¿Es la versión v2.3.7 específicamente? | Se probó `v2.3.6` (downgrade) y `2.4.0-rc2` (upgrade, con activación de licencia gratuita completada) — mismo error exacto en ambas. |
| ¿Es un bloqueo específico a los números ya usados en las pruebas? | Descartado — un número que **nunca** le había escrito a este WhatsApp también falló idéntico en su primer intento. |
| ¿Es temporal, se levanta solo con tiempo? | Descartado — repetido **12+ horas después**, mismo error exacto, cero cambio. |
| ¿Ayudaría cambiar de número (SIM nueva)? | No verificado con una SIM real todavía, pero descartado por razonamiento fuerte: la falla es 100% reproducible e instantánea en todos los casos probados — patrón consistente con un hueco de implementación del cliente (no envía el campo que exige WhatsApp), no con una restricción específica de cuenta. Cualquier número corriendo este mismo software probablemente fallaría igual en su primer intento con un contacto nuevo. |
| ¿Es específico de Baileys? ¿Cambiar de motor ayudaría? | Descartado — investigado a fondo. **Evolution Go** (motor en Go, librería `whatsmeow`) tiene el mismo issue abierto y sin resolver: [evolution-go#50](https://github.com/evolution-foundation/evolution-go/issues/50), causa raíz idéntica confirmada también en [whatsmeow#1074](https://github.com/tulir/whatsmeow/issues/1074). **OpenWA** con motor `whatsapp-web.js` (navegador real en vez de reimplementar el protocolo) tiene el mismo problema de fondo manifestándose peor: bloqueos de cuenta completos en vez de un mensaje rechazado limpio ([whatsapp-web.js#3250](https://github.com/wwebjs/whatsapp-web.js/issues/3250), [#1872](https://github.com/pedroslopez/whatsapp-web.js/issues/1872)). |

## 5b. Actualización — comparación real de versiones de Baileys (21 de agosto)

Un colega del equipo técnico contrastó el diagnóstico contra el estado actual de Baileys en
GitHub y señaló algo importante: el manejo de TC tokens/Reachout Timelock se agregó
específicamente en `v7.0.0-rc.10` (mayo 2025), y no hay garantía de que las versiones de
Evolution API probadas incluyan esa versión de Baileys o una posterior. Se verificó
directamente, revisando el `package.json` de Baileys empaquetado dentro de cada imagen (sin
correr ninguna, solo inspección de archivos):

| Imagen de Evolution API | Baileys empaquetado | ¿Incluye el fix de TC token (rc.10+)? |
|---|---|---|
| `v2.3.6` | `7.0.0-rc.6` | ❌ No |
| `v2.3.7` (la que usamos) | `7.0.0-rc.9` | ❌ No — justo la versión anterior al fix |
| `2.4.0-rc2` | `7.0.0-rc.9` | ❌ No — Evolution ni siquiera actualizó Baileys en este bump |
| `latest` | `7.0.0-rc.9` | ❌ No |
| `homolog` (canal de pre-lanzamiento oficial) | `7.0.0-rc13` | ✅ Sí |

**Confirmado: ninguna de las versiones estables/RC probadas hasta ahora incluye el fix real.**
Esto valida la hipótesis del colega — nunca se descartó el fix en sí, se descartaron versiones
de Evolution API que nunca lo tuvieron empaquetado.

### Intento con `evoapicloud/evolution-api:homolog`

Se hizo backup de la base de datos de Postgres y del volumen de instancias antes de tocar nada.
Al intentar levantar `homolog`, la imagen entra en bucle de reinicio por un **problema de
empaquetado distinto y no relacionado con Baileys/463**: incluye Prisma `7.8.0` (salto de
versión mayor), pero el archivo `prisma/postgresql-schema.prisma` empaquetado no tiene la línea
`url = env(...)` en el bloque `datasource`, y tampoco existe un `prisma.config.ts` — Prisma 7.x
exige uno de los dos para `migrate deploy`. Confirmado inspeccionando los archivos dentro de la
imagen directamente:

```
datasource db {
  provider = "postgresql"
}
```

(sin `url`). Se probó pasar `DATABASE_URL`/`DATABASE_CONNECTION_URI` de varias formas
(`environment:` de compose, archivo `.env` real vía `--env-file`) — la variable sí llega
correctamente al proceso (confirmado en el log: `Database URL: postgresql://...`), pero Prisma
igual falla porque el schema empaquetado no la referencia. Es un bug de empaquetado de este tag
específico, no algo resoluble desde afuera del contenedor sin parchear el archivo del schema.

**Se revirtió a `v2.3.7` de inmediato** (sesión de WhatsApp intacta, sin pérdida de datos — la
migración nunca llegó a tocar la base de datos real porque falló antes de ejecutarse).

### Sobre la imagen `deployfybr/evolution:latest` sugerida por un compañero

Se verificó la información pública del publicador antes de considerar ejecutarla contra el
número real:

- **188 descargas totales, 0 estrellas**, cuenta de Docker Hub registrada el 2026-07-28 (menos
  de un mes).
- `"source": null` — no vinculada a ningún repositorio público. No hay Dockerfile ni build
  auditable visible en ningún lado.
- Sin descripción, sin discusión pública encontrada sobre esta imagen específica en ningún
  issue tracker o foro.

**No se ejecutó.** El perfil de riesgo (publicador desconocido, cero transparencia sobre el
contenido real, recomendada solo de oídas) no se justifica todavía frente al riesgo de correrla
con las credenciales reales de WhatsApp de la empresa. Si se quiere insistir en esta vía, lo
mínimo indispensable sería conseguir el repositorio fuente real (si existe) y revisar el diff
contra `evoapicloud/evolution-api` antes de correrla, nunca a ciegas.

## 5c. Intento de parche del bug de Prisma en `homolog` (21 de agosto) — parcialmente exitoso, descubre un bloqueador nuevo

Se intentó arreglar directamente el bug de empaquetado de Prisma descrito en 5b, **en un entorno
completamente aislado** (Postgres desechable en una red Docker separada, sin tocar en ningún
momento el Postgres/volumen reales que sirven la sesión de WhatsApp de producción), antes de
considerar tocar la instancia real.

**Diagnóstico más preciso que en 5b:** no es solo que falte `url = env(...)` en el schema. Prisma
`7.8.0` **rechaza activamente** ese campo dentro del `.prisma` — es un cambio de comportamiento
deliberado de Prisma 7, no un descuido:

```
error: The datasource property `url` is no longer supported in schema files. Move connection
URLs for Migrate to `prisma.config.ts` and pass either `adapter` for a direct database
connection or `accelerateUrl` for Accelerate to the `PrismaClient` constructor.
```

Prisma 7 movió la URL de conexión del archivo de schema a un archivo de configuración nuevo,
`prisma.config.ts`, en la raíz del proyecto. La imagen `homolog` **sí incluye las dependencias
necesarias** para ese patrón (`@prisma/config`, `@prisma/adapter-pg`, `@prisma/adapter-mariadb`
ya están en `node_modules` y en `package.json`) — lo que falta es, literalmente, el archivo
`prisma.config.ts` en sí. Es un paso de release que el equipo de Evolution Foundation no incluyó
en este tag pre-release.

**Fix aplicado y probado:** se montó por bind-mount un `prisma.config.ts` mínimo en la raíz del
contenedor (`/evolution/prisma.config.ts`), sin tocar el `.prisma` original:

```ts
import { defineConfig, env } from '@prisma/config';

export default defineConfig({
  schema: './prisma/postgresql-schema.prisma',
  datasource: {
    url: env('DATABASE_CONNECTION_URI'),
  },
});
```

Resultado, contra un Postgres 15 desechable y vacío: `npm run db:deploy` corrió las 20+
migraciones sin error ("All migrations have been successfully applied. Migration succeeded"),
`npm run db:generate` generó el cliente de Prisma correctamente, y el proceso arrancó,
levantando el servidor HTTP en el puerto 8080. **El bug de Prisma en sí queda confirmado como
arreglable** con este archivo, sin tocar el schema ni el código fuente de Evolution API.

**Bloqueador nuevo, no relacionado con Prisma ni con el 463, encontrado de inmediato al probar
un endpoint funcional real:**

```json
GET /instance/fetchInstances → HTTP 503
{
  "error": "service not activated",
  "code": "LICENSE_REQUIRED",
  "register_url": "http://localhost:8080/manager/login",
  "message": "This Evolution API instance is not activated. Open .../manager/login to activate,
   or set AUTHENTICATION_API_KEY in your .env with a valid licensing key."
}
```

Investigado contra la documentación oficial (`docs.evolutionfoundation.com.br/licensing`):

- **Desde Evolution API 2.4.0 en adelante** (`homolog` se reporta internamente como versión
  `2.4.0`; **`2.4.0-rc2`, que ya habíamos probado y descartado en la sección 5 por el 463, cae en
  esta misma regla**), Evolution Foundation exige activar cada instancia contra su propio
  servidor de licencias antes de que los endpoints funcionales respondan — antes de eso, todo
  responde 503. `v2.3.7` (< 2.4.0) no tiene esta exigencia, por eso nunca la vimos en ninguna
  prueba anterior.
- Es **gratuito** ("todos os tiers `community` são gratuitos, sem limite de instâncias, sem
  limite de mensagens", según su propia documentación) — no es un muro de pago.
- Requiere registrar un email de operador contra su servidor. Existe un flujo headless
  (`EVOLUTION_OPERATOR_EMAIL` en el entorno → POST automático a `/v1/register/auto`) que evita el
  navegador, **pero solo después de que ese email ya fue activado una vez por el flujo manual**
  (navegador, Magic Link/OAuth) — la primera activación de un email nuevo no se puede automatizar
  del todo.
- Telemetría obligatoria una vez activada (no hay opción documentada para desactivarla): un
  payload de activación (instance_id, versión, IP/GeoIP del operador) y un heartbeat cada 5
  minutos (instance_id, conteo de mensajes enviados, lista de features activas). Su documentación
  afirma explícitamente que **no** envían contenido de mensajes, números de contacto, IDs de
  conversación, medios, API keys ni credenciales de base de datos — pero sigue siendo tráfico
  saliente constante hacia un tercero desde una instancia con datos reales de clientes.

**Nota relevante:** ya se completó una activación gratuita contra este mismo servidor de
licencias antes, al subir a `2.4.0-rc2` (ver sección 5, "activación gratuita completada"). Si fue
con el mismo email, `homolog` probablemente podría activarse sin pasar de nuevo por el navegador,
usando `EVOLUTION_OPERATOR_EMAIL` con ese email ya conocido — no confirmado todavía, no se
intentó porque implica volver a interactuar con el servidor real de un tercero y se decidió
pausar para reportar este hallazgo primero.

**Estado real al cierre de 5c: NO confirmado que Baileys `rc13` resuelva el 463.** Se demostró que
`homolog` puede arrancar y correr migraciones correctamente con el parche de Prisma, pero nunca
se llegó a probar el envío de un mensaje real — el muro de licencia lo impide. No se ha tocado la
instancia de producción (`v2.3.7`, sesión de WhatsApp real intacta) en ningún momento de esta
prueba; todo lo anterior se hizo contra un Postgres/red Docker completamente desechables.

## 5d. Continuación — se pasó el muro de licencia, pero un bug distinto en la creación de la instancia impidió llegar a probar el 463

Con autorización explícita para continuar, se completó la activación de licencia (en el mismo
entorno aislado, Postgres/red Docker desechables, sin tocar la instancia real) y se intentó llegar
hasta el punto de conectar una sesión real y probar el 463 con Baileys `rc13`.

**Activación de licencia — funcionó, más simple de lo esperado.** Se llamó directamente al
endpoint de activación automática del servidor de licencias
(`POST https://license.evolutionfoundation.com.br/v1/register/auto`, con `email`, `tier`,
`version`, `instance_id`) usando `EVOLUTION_OPERATOR_EMAIL=keveenrodriguez@gmail.com`. Respondió
`200 OK` con una API key de licencia activa en el primer intento — no fue necesario el flujo
manual de navegador que la documentación describe como obligatorio para un email nuevo (`tier:
"community"`, gratuito, sin límite de instancias ni mensajes). Se reinició el contenedor de
prueba con esa API key como `AUTHENTICATION_API_KEY`; el log confirmó
`"Global API key accepted — license saved and activated"`, y `GET /instance/fetchInstances`
respondió `200 []` en vez del `503 LICENSE_REQUIRED` anterior. **El muro de licencia queda
confirmado como superable**, sin fricción real en este caso puntual.

**Bloqueador nuevo, un cuarto bug independiente — la creación de la instancia con
`integration: "WHATSAPP-BAILEYS"` falla siempre, desde el primer intento:**

```
POST /instance/create
{"instanceName": "...", "integration": "WHATSAPP-BAILEYS", "qrcode": true}

→ HTTP 400
"Invalid `r.integrationSession.update()` invocation ... Foreign key constraint violated
 on the constraint: `Setting_instanceId_fkey`"
```

Reproducido de forma **100% consistente**, tres veces, con nombres de instancia distintos y con
variaciones del payload (sin `qrcode`, con los campos de `settings` — `rejectCall`,
`groupsIgnore`, `alwaysOnline`, `readMessages`, `readStatus`, `syncFullHistory` — pasados
explícitamente): siempre el mismo error. Confirmado directo en la base de datos de prueba
(`SELECT * FROM "Instance"` → 0 filas después de cada intento) que la instancia **nunca llega a
crearse**, ni parcialmente — no es un estado corrupto dejado por un intento anterior, falla desde
cero cada vez. El stack trace apunta a `saveInstance()` (llamado desde `createInstance()`)
intentando escribir un registro relacionado (`Setting`, que tiene `instanceId` como FK `NOT NULL`
+ `UNIQUE`) antes de que el `Instance` referenciado exista — un bug de orden de escritura dentro
del código ya compilado (`dist/main.js`) de esta imagen, no algo influenciable desde el payload de
la petición, variables de entorno, o un archivo de configuración montado. A diferencia de los
otros dos bugs de `homolog` (Prisma, licencia), este vive dentro del bundle minificado de la
aplicación — no hay una forma razonable de parchearlo desde afuera sin recompilar el proyecto
desde su código fuente real.

**Se detuvo el experimento en este punto.** No se llegó a generar ningún QR, no se llegó a
conectar ninguna sesión de WhatsApp, y por lo tanto **tampoco se llegó a probar el envío de un
mensaje real**. La tabla comparativa que tiene más valor informativo, siguiendo el formato
sugerido, queda así — con `homolog` en blanco porque el experimento nunca llegó a esa etapa:

| | `v2.3.7` (evidencia ya existente, sección 5) | `homolog` (este intento) |
|---|---|---|
| Baileys | `7.0.0-rc.9` | `7.0.0-rc13` |
| Licencia requerida | No aplica (< 2.4.0) | Sí — superada |
| Instancia WHATSAPP-BAILEYS creada | Sí | **No — falla siempre, bug de FK en `Setting`** |
| Contacto frío → respuesta | ❌ (463) | No alcanzado |
| HTTP de `/message/sendText` | 201 | No alcanzado |
| `status`/`messageStubParameters` | `0` / `["463"]` | No alcanzado |
| Entrega física al teléfono | ❌ | No alcanzado |

Entorno de prueba desmontado por completo al terminar (contenedores, red, volumen — todo
desechable). La instancia de producción (`v2.3.7`) nunca se tocó, sesión real intacta durante
todo el proceso.

## 6. Conclusión y lo que se necesita del equipo técnico

Es una restricción del lado de los servidores de WhatsApp contra clientes no oficiales que
intentan responder a contactos nuevos/en frío, expuesta por un hueco de implementación
(persistencia/reenvío de `tctoken`/`cstoken`) presente en **las tres librerías/motores no
oficiales investigados** (Baileys, whatsmeow, whatsapp-web.js) — pero con una precisión
importante confirmada el 21 de agosto: **ninguna versión de Evolution API que hemos podido
probar hasta ahora incluye el Baileys posterior al fix** (todas empaquetan `rc.6`-`rc.9`; el
fix llegó en `rc.10`). La única que sí lo trae (`homolog`, oficial, internamente versión
`2.4.0`) resultó tener **tres bugs de release independientes**, encontrados uno tras otro al ir
resolviendo cada uno: (1) Prisma sin `datasource.url`/`prisma.config.ts` — **arreglado** con un
`prisma.config.ts` propio; (2) activación de licencia obligatoria — **superada**, activación
gratuita exitosa vía `EVOLUTION_OPERATOR_EMAIL`; (3) `POST /instance/create` con
`integration: "WHATSAPP-BAILEYS"` falla siempre con un error de foreign key
(`Setting_instanceId_fkey`) dentro del código ya compilado — **sin arreglar, no hay forma
razonable de parchearlo desde afuera del contenedor**. Este tercer bug es, hoy, el que
efectivamente bloquea la prueba: nunca se llegó a crear una instancia, generar un QR, conectar
una sesión, ni enviar un mensaje real. **El 463 sigue sin confirmarse resuelto ni descartado con
Baileys ≥ rc.10** — no por el 463 mismo, sino porque el canal (`homolog`) que lo trae está roto
en un punto anterior y no relacionado.

Preguntas concretas para el equipo técnico:
1. ¿Alguien del equipo tiene acceso a una imagen o build de Evolution API con Baileys ≥
   `7.0.0-rc.10` en la que `POST /instance/create` con `integration: "WHATSAPP-BAILEYS"` **sí
   funcione**? Con tres bugs de release distintos ya encontrados en `homolog` (Prisma, licencia,
   y ahora la creación de instancia), ¿es este canal realmente usable para pruebas, o es
   demasiado inestable incluso para eso?
2. Específicamente sobre el bug de la sección 5d (`Setting_instanceId_fkey`) — ¿es un bug conocido
   del equipo de Evolution Foundation? ¿Hay un issue público o un workaround (una tabla `Setting`
   que se pueda pre-poblar a mano, una migración pendiente, un flag que desactive esa escritura)?
3. ¿Conocen alguna forma de conseguir una imagen de Evolution API funcional con Baileys ≥
   `7.0.0-rc.10` que **no** sea `homolog` — build propio, otro tag, o un release estable más
   reciente que no hayamos visto?
4. ¿Hay alguna otra integración/gateway de WhatsApp (fuera de Baileys/whatsmeow/whatsapp-web.js)
   con historial confirmado de **no** tener este problema?
5. ¿Vale la pena evaluar otras alternativas de API como openWA (https://github.com/rmyndharis/OpenWA), WAHA (https://github.com/devlikeapro/waha - https://waha.devlike.pro/), Evolution API Go (https://github.com/evolution-foundation/evolution-go)?
6. Sobre `deployfybr/evolution:latest` (sugerida por un compañero): ¿alguien puede confirmar el
   repositorio fuente real detrás de esa imagen? Sin eso no es prudente correrla contra
   credenciales reales — ver sección 5b para el detalle de por qué.

## 7. Posibles soluciones — propuestas nuestras, ninguna confirmada aún

Ninguna de las siguientes se ha probado contra el escenario real (mensaje de un contacto nuevo) —
el bug de la sección 5d lo impidió. Se listan en el orden en que las probaríamos:

**A. Intentar entender/parchar el bug de `Setting_instanceId_fkey` sin recompilar `homolog`
desde cero.** Por ejemplo, insertando a mano en la base de prueba una fila `Setting` con el
`instanceId` esperado justo antes de llamar `/instance/create` (si el flujo interno hace un
`UPDATE` en vez de un `INSERT` cuando la fila ya existe, esto podría rodear el bug sin tocar el
binario). No confirmado, es una hipótesis a probar en el mismo entorno aislado.

**B. Pedirle directamente al equipo de Evolution Foundation (vía su Discord/soporte oficial, no
solo a este equipo técnico externo) que confirme si `homolog` es realmente usable hoy, o esperar
una build más estable del mismo canal.** Dado que ya son tres bugs distintos en la misma imagen,
es razonable sospechar que este tag específico está roto más allá de lo que vale la pena
parchear nosotros mismos.

**C. Esperar una versión estable de Evolution API ≥ 2.4.0** (no pre-release) una vez que
Evolution Foundation publique una con Baileys ≥ rc.10 y sin estos bugs — evita depender de
`homolog` para cualquier cosa, prueba o producción. El costo es tiempo de espera, no ingeniería.

**D. Si (A) o (B) logran una instancia `WHATSAPP-BAILEYS` funcional con Baileys ≥ rc.10, retomar
el plan original:** conectar la sesión real, probar con un contacto genuinamente frío, y llenar
la tabla comparativa de la sección 5d. Solo si eso confirma que el 463 se resuelve, evaluar migrar
la instancia real de `v2.3.7`.

**E. Si ninguna vía anterior da una imagen funcional en un tiempo razonable**, esto empieza a leer
como que la ruta Evolution API/Baileys — incluso con el fix de Baileys existiendo en teoría — no
es viable en la práctica por la calidad del empaquetado del proyecto, y la alternativa de fondo
pasa a ser la API oficial de WhatsApp Business de Meta (de pago, requiere aprobación) o revisar de
nuevo whatsmeow/whatsapp-web.js por si tienen una versión más nueva sin este problema.

**F. Alternativa de bajo riesgo mientras se decide lo anterior:** seguir operando con `v2.3.7`
tal como está hoy (sin cambios, sesión real intacta) y tratar el 463 como un riesgo conocido y
aceptado a corto plazo — ya está así en `PROJECT_STATE.md`, no requiere ninguna acción adicional.

Nuestra recomendación, si el equipo técnico no objeta: intentar (A) primero, en aislamiento total
de la instancia real, porque es el único paso que realmente responde la pregunta que todo este
reporte viene persiguiendo — si es Baileys `rc13`, y no otra cosa, lo que resuelve el 463.
