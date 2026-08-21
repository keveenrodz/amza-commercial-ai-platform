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

## 5e. Causa raíz exacta del bug de 5d — no es solo el FK, es un filtro anti-tampering mal aplicado

Antes de intentar cualquier workaround "a ciegas" (como pre-crear una fila `Setting`), se
inspeccionó el código fuente real dentro del bundle compilado (`/evolution/dist/main.js`, de
solo lectura, sin ejecutar nada inseguro) para entender exactamente qué falla. Esto reveló que
el error de foreign key visible en el response **no es el error real** — es un efecto
secundario de un error anterior que la aplicación captura y solo registra en el log, sin
propagarlo:

```js
async saveInstance(t){
  try{
    let A = await this.configService.get("DATABASE").CONNECTION.CLIENT_NAME;
    await this.prismaRepository.instance.create({data:{
      id: t.instanceId, name: t.instanceName, ownerJid: t.ownerJid, ...
    }})
  } catch(A) { this.logger.error(A) }   // <- el error real se traga aquí, solo se loguea
}
```

El log completo (no visible en la respuesta HTTP, solo en `docker logs`) mostró el error real:

```
PrismaClientValidationError
Invalid `this.prismaRepository.instance.create()` invocation
data: { id: "...", ownerJid: undefined, ..., integration: "WHATSAPP-BAILEYS", ...,
+   name: String }
Argument `name` is missing.
```

Es decir: `t.instanceName` llegó `undefined` a `saveInstance()`, así que la fila `Instance`
**nunca se crea** (el error se traga y el código sigue adelante como si hubiera funcionado).
El siguiente paso, `settingsService.create()`, intenta escribir un `Setting` apuntando a un
`instanceId` que nunca llegó a existir — de ahí el error de foreign key que sí llega al cliente.
(Nota aparte: el mensaje de ese segundo error dice que la llamada que falló fue
`integrationSession.update()`, en una ubicación de código totalmente distinta — casi seguro un
bug del propio formateador de errores de Prisma 7.8.0 con este bundle sin sourcemaps correctos,
no algo en lo que vale la pena profundizar más; el error de FK en sí, y su causa real, están
confirmados igual con el log completo).

**¿Por qué llega `undefined`?** Justo antes del error, en cada uno de los 3 intentos, apareció
este log: `WARN [Validate] Ignoring attempt to override protected field "instanceName" via
untrusted input` — buscando esa cadena literal en el bundle se encontró la función responsable:

```js
var Cd = ["instanceName", "instanceId"];   // campos "protegidos"
function ug(o) {
  // filtra estos campos de cualquier objeto de entrada, avisando por log
  for (let [A, e] of Object.entries(o)) {
    if (Cd.includes(A)) { Ze.warn(`Ignoring attempt to override protected field "${A}"...`); continue }
    t[A] = e
  }
  return t
}
// dentro de dataValidate():
A.originalUrl.includes("/instance/create") && Object.assign(r, ug(i))   // i = A.body
```

Esta protección tiene sentido para rutas que identifican la instancia por la URL (ej.
`/instance/connect/:instanceName`) — evita que alguien mande un `instanceName` distinto en el
body para intentar operar sobre otra instancia. **El bug es que esta misma regla se aplica
también a `/instance/create`**, la única ruta donde el cliente **tiene que** poder mandar
`instanceName` — es el único lugar donde se define, no hay ningún otro valor "legítimo" que
proteger todavía. Aplicar ahí ese filtro parece un error de alcance (código pensado para otras
rutas, aplicado también a esta por descuido), no una decisión de diseño.

**No es parchable desde afuera del contenedor.** A diferencia del bug de Prisma (un archivo de
config faltante) y del muro de licencia (una llamada HTTP a un servidor externo), esto vive
dentro de la lógica de validación ya compilada — no hay una variable de entorno, un archivo
montado, ni una forma distinta de armar la petición HTTP que lo evite (se confirmó que tanto
mandar `instanceName` normal como agregar los campos de `settings` explícitos producen el mismo
resultado). Arreglarlo requeriría modificar el código fuente real de Evolution API y
recompilar — algo que está fuera de lo razonable para nuestro equipo hacer sobre un canal
pre-release de un tercero.

## 5f. El bug ya es público y ya tiene un fix escrito — pero está atascado sin mergear

Antes de reportarlo como un hallazgo nuevo, se buscó en el repositorio real
(`evolution-foundation/evolution-api`, GitHub) si alguien ya lo había documentado. Resultado:
**sí, dos veces — como issue reportado por la comunidad y como PR con el fix ya escrito y
aprobado por un mantenedor, pero nunca mergeado.**

**Issue [#2631](https://github.com/evolution-foundation/evolution-api/issues/2631)** (abierto,
sin resolver): reporta exactamente el mismo error (`Setting_instanceId_fkey`, instalación
completamente limpia, Postgres y Redis recién creados), reproducido de forma independiente en
`2.4.0`, `2.4.0-rc2` y `homolog`. Comentarios de la comunidad: alguien reporta que en su caso solo
pasa en `homolog` (contradice parcialmente al autor original, que dice reproducirlo también en
`2.4.0`/`2.4.0-rc2` — no hay consenso claro sobre el alcance exacto entre versiones, pero coincide
con nuestro hallazgo en que `homolog` sí lo tiene siempre).

**PR [#2608](https://github.com/evolution-foundation/evolution-api/pull/2608)** (`fix: instance
creation broken by sanitization guard and silent error swallow`, contra `develop`, autor externo
`pastoriniMatheus`): el diagnóstico del PR **coincide palabra por palabra** con lo que encontramos
de forma independiente leyendo el bundle compilado — mismo mecanismo exacto (`sanitizeUntrustedInput`/
`PROTECTED_INSTANCE_FIELDS` filtrando `instanceName` en `/instance/create`, `saveInstance()`
tragando el error sin relanzarlo). El PR además corrige, en un segundo commit, **el mismo bug de
Prisma que nosotros arreglamos con `prisma.config.ts`** (`Dockerfile` no copiaba
`prisma.config.ts` a la imagen final) y un problema adicional no probado por nosotros (`?schema=`
en la URL de conexión rompe las queries generadas por Prisma 7 con adaptador).

Se verificó el estado real del PR, no solo el diff:
- **Un mantenedor externo (`dpaes`) lo revisó línea por línea, confirmó el diagnóstico contra
  `develop` directamente, y lo aprobó** (`APPROVED`, 2026-06-28) tras una ronda de cambios.
- **Sigue sin mergear, casi dos meses después** (última actividad: 2026-06-28; hoy es
  2026-08-21). La razón: el check obligatorio de CI (`check-lint-and-build`) falla — pero por un
  problema de configuración del propio pipeline de CI de Evolution Foundation (no popula
  `DATABASE_CONNECTION_URI`, que `prisma.config.ts` ahora exige — el mismo tipo de problema de
  Prisma 7 que nos costó a nosotros), confirmado por el propio revisor como **preexistente en
  `develop`, no causado por este PR**. Es un bloqueo de infraestructura de CI, no del código.
- Se confirmó directamente contra el código fuente de `develop` (no solo el diff del PR) que **el
  bug sigue presente hoy, sin mergear** (`src/api/abstract/abstract.router.ts` y
  `src/api/services/monitor.service.ts` en `develop` tienen exactamente el código roto).
- El commit específico del PR (`45d3122ca998b7d26b5153cb97984509e3289b92`) declara
  `"baileys": "7.0.0-rc13"` en su `package.json` — **es decir, ese commit exacto tiene ambas
  cosas a la vez: el fix de creación de instancia Y Baileys posterior al fix de TC token.**
- No existe ninguna imagen Docker publicada (revisado el listado completo de tags en Docker Hub)
  construida desde ese commit o esa rama — solo existe como código fuente en GitHub.

**Esto cambia la opción "build propia" de especulativa a concreta y de bajo riesgo relativo:** a
diferencia de `deployfybr/evolution:latest` (código no auditable, publicador desconocido), este
commit es 100% público, del repositorio oficial, con diff visible línea por línea, y ya revisado
y aprobado por un mantenedor humano independiente — el riesgo de cadena de suministro es
comparable al de cualquier release oficial, no al de una imagen de origen desconocido.

## 5g. Se construyó la imagen y se probó de verdad — primera entrega confirmada a un contacto frío

Se construyó una imagen Docker propia desde el commit exacto del PR #2608
(`45d3122ca998b7d26b5153cb97984509e3289b92`, usando el `Dockerfile` real del repositorio, sin
modificarlo) y se probó en el mismo estilo de entorno aislado usado en toda esta investigación
(Postgres desechable, red Docker propia).

1. **`prisma.config.ts` ya viene incluido en la imagen final** (ese era precisamente el fix #5 del
   PR) — no hizo falta ningún parche adicional de nuestra parte. Migraciones corrieron limpio.
2. **Activación de licencia**, mismo mecanismo que en 5d (`EVOLUTION_OPERATOR_EMAIL`,
   `/v1/register/auto`) — funcionó igual, gratuita, con el mismo `customer_id` ya conocido.
3. **`POST /instance/create` con `integration: "WHATSAPP-BAILEYS"` respondió `201 Created`** —
   el bug de la sección 5e/5f **queda confirmado como arreglado** en este commit, no solo en
   teoría. Instancia creada, QR generado sin problema.
4. **Con autorización explícita, se conectó el número real de negocio** (+57 301 509 2386) vía
   QR. Efecto secundario real: la sesión de producción (`v2.3.7`) quedó desconectada
   (`connectionStatus: "close"`) — no fue un dispositivo vinculado en paralelo, sustituyó la
   sesión activa. Recuperable (se puede reconectar `v2.3.7` volviendo a escanear ahí), pero
   importante dejarlo documentado como el costo real de esta prueba, no algo gratis.
5. **Un contacto que nunca le había escrito antes a este número envió un mensaje real**
   (dirección LID: `128849086042212@lid` / `573116387935@s.whatsapp.net` — el propio formato de
   direccionamiento que Baileys ≥ rc.10 maneja distinto, ver sección 2). Se respondió manualmente
   vía `POST /message/sendText` (sin backend/IA de por medio — la prueba mide el comportamiento
   del protocolo, no nuestra integración).
6. **Resultado: `HTTP 201`, `status: 1` (PENDING) sin `messageStubParameters` — nunca apareció el
   463 en los logs, ni error de ningún tipo, en los más de dos minutos que se esperó.** Y lo más
   importante: **la persona que envió el mensaje original confirmó directamente que el mensaje
   de respuesta le llegó a su teléfono.** Es la primera entrega real confirmada a un contacto
   frío en toda esta investigación.

Tabla comparativa final, con el formato pedido:

| | `v2.3.7` (producción, evidencia sección 5) | Build `45d3122` (PR #2608, este intento) |
|---|---|---|
| Baileys | `7.0.0-rc.9` | `7.0.0-rc13` |
| Licencia requerida | No aplica (< 2.4.0) | Sí — superada |
| `instance/create` | ✅ | ✅ (antes fallaba en `homolog`, aquí ya arreglado) |
| QR / conexión | ✅ | ✅ |
| Contacto frío → respuesta | ❌ (463) | **✅ entregado, confirmado por el receptor** |
| HTTP de `/message/sendText` | 201 | 201 |
| `status`/`messageStubParameters` | `0` / `["463"]` | `1` (PENDING) / `[]` (vacío) |
| Entrega física al teléfono | ❌ | **✅ confirmada** |

**Esto es evidencia real, no solo de logs, de que el cambio de versión de Baileys (rc9→rc13, que
incluye el manejo de TC token/Reachout Timelock y direccionamiento LID) está causalmente
relacionado con la resolución del 463** para este escenario concreto de contacto frío. Sigue
siendo **una sola prueba, un solo contacto** — antes de considerar esto validado para producción,
la recomendación (propia y del equipo técnico externo) es repetir con 2-3 contactos fríos más,
una conversación de varias vueltas, un reinicio del contenedor (confirmar que la sesión
sobrevive), y verificar el comportamiento tras una reconexión — recién después de eso evaluar
migrar la instancia real, con backup previo. Ninguna de esas rondas adicionales se ha hecho
todavía.

## 6. Conclusión y lo que se necesita del equipo técnico

Es una restricción del lado de los servidores de WhatsApp contra clientes no oficiales que
intentan responder a contactos nuevos/en frío, expuesta por un hueco de implementación
(persistencia/reenvío de `tctoken`/`cstoken`) presente en **las tres librerías/motores no
oficiales investigados** (Baileys, whatsmeow, whatsapp-web.js) — pero con una precisión
importante confirmada el 21 de agosto: **ninguna versión de Evolution API previamente probada
incluía el Baileys posterior al fix** (todas empaquetan `rc.6`-`rc.9`; el fix llegó en `rc.10`).

**Actualización final — probado de verdad, con resultado positivo (ver sección 5g).** Se
construyó una imagen propia desde el commit exacto de
[PR #2608](https://github.com/evolution-foundation/evolution-api/pull/2608)
(`45d3122ca998b7d26b5153cb97984509e3289b92`, fix ya escrito, revisado y aprobado por un
mantenedor, solo sin mergear por un problema de CI no relacionado con el código) — un commit que
trae a la vez el fix de creación de instancia (issue
[#2631](https://github.com/evolution-foundation/evolution-api/issues/2631)) y Baileys
`7.0.0-rc13`. Con autorización explícita, se conectó el número real de negocio y se probó contra
un contacto genuinamente frío: **`HTTP 201`, sin error 463 en los logs, y la persona que envió el
mensaje original confirmó directamente que la respuesta le llegó a su teléfono.** Es la primera
entrega real confirmada a un contacto frío en toda esta investigación.

**Esto es evidencia real y positiva de que el cambio de versión de Baileys está causalmente
relacionado con el 463** — pero sigue siendo una sola prueba con un solo contacto. Antes de
considerar esto resuelto para producción, falta repetir con 2-3 contactos más, una conversación
de varias vueltas, un reinicio del contenedor, y verificar el comportamiento tras una
reconexión — ninguna de esas rondas se ha hecho todavía. Efecto secundario real ya documentado:
conectar el número real a esta instancia de prueba desconectó la sesión de producción
(`v2.3.7`), recuperable pero no gratis.

**Decisión tomada:** se deja de intentar parchar `homolog` (ya no es necesario, la build propia
del commit del PR #2608 lo reemplaza con una base sin esos tres bugs). El foco pasa a: (a)
completar las rondas de validación adicionales sobre esta misma build antes de decidir sobre
producción, y (b) escalar el hallazgo y este resultado positivo al equipo técnico/Evolution
Foundation — con evidencia real de que su propio fix (PR #2608) + Baileys rc13 resuelve el
problema que motivó todo este reporte, es un dato valioso para que ellos también prioricen
mergearlo.

Preguntas concretas para el equipo técnico:
1. Sobre [PR #2608](https://github.com/evolution-foundation/evolution-api/pull/2608) — ¿alguien
   puede empujar para que se mergee (el bloqueo es un problema de CI, no del código, ya
   confirmado por el propio revisor), o confirmar si hay alguna razón para no hacerlo que no
   veamos desde afuera?
2. ¿Alguien tiene experiencia construyendo su propia imagen de Evolution API desde un commit
   específico (Dockerfile del propio repo) para producción, en vez de depender de los tags
   oficiales? ¿Hay algo no evidente en ese proceso que debamos saber?
3. ¿Hay alguna otra integración/gateway de WhatsApp (fuera de Baileys/whatsmeow/whatsapp-web.js)
   con historial confirmado de **no** tener este problema?
4. ¿Vale la pena evaluar otras alternativas de API como openWA (https://github.com/rmyndharis/OpenWA), WAHA (https://github.com/devlikeapro/waha - https://waha.devlike.pro/), Evolution API Go (https://github.com/evolution-foundation/evolution-go)?
5. Sobre `deployfybr/evolution:latest` (sugerida por un compañero) — con el commit del PR #2608
   ya identificado como alternativa pública y auditable, ¿sigue teniendo sentido perseguir
   `deployfybr`? Si el compañero puede dar de todas formas repositorio/commit/versión de Baileys,
   lo evaluamos; si no, con esta alternativa disponible probablemente ya no haga falta.

## 7. Posibles soluciones — propuestas nuestras, ninguna confirmada aún

Ninguna de las siguientes se ha probado contra el escenario real (mensaje de un contacto nuevo).
Orden recomendado, actualizado tras encontrar el PR #2608:

**A. Construir una imagen Docker propia desde el commit del PR #2608**
(`45d3122ca998b7d26b5153cb97984509e3289b92`), usando el `Dockerfile` oficial del propio
repositorio, en el mismo entorno de prueba aislado (Postgres/red Docker desechables). Es la
opción con mejor relación evidencia/riesgo hoy: código público, diff auditado línea por línea,
aprobado por un mantenedor humano, y con la combinación exacta que necesitamos (fix de instancia
+ Baileys `rc13`). Distinto de todo lo intentado hasta ahora — es la primera vez que
construiríamos una imagen nosotros mismos en vez de usar una ya publicada.

**B. En paralelo, pedir en el propio PR/issue de GitHub que se mergee** — el bloqueo es de CI,
no del código (confirmado por el revisor), así que empujarlo podría destrabarlo sin que
nosotros necesitemos construir nada.

**C. Pedirle al compañero que sugirió `deployfybr/evolution:latest` el repositorio/commit/
Dockerfile exacto** — con (A) disponible como alternativa pública y auditable, esto pierde
prioridad, pero se mantiene abierto si puede dar esa evidencia igual.

**D. Si (A) o (B) dan una instancia `WHATSAPP-BAILEYS` funcional con Baileys ≥ rc.10, retomar
el plan original:** conectar la sesión real, probar con un contacto genuinamente frío, y llenar
la tabla comparativa de la sección 5d. Solo si eso confirma que el 463 se resuelve, evaluar migrar
la instancia real de `v2.3.7`.

**E. Si (A) tampoco resuelve el 463** (es decir, ni con el fix de instancia ni con Baileys rc13
desaparece el bloqueo), eso cierra definitivamente la vía Evolution API/Baileys como arreglable
con una actualización de versión, y la alternativa de fondo pasa a ser la API oficial de WhatsApp
Business de Meta (de pago, requiere aprobación) o revisar de nuevo whatsmeow/whatsapp-web.js por
si tienen una versión más nueva sin este problema.

**F. Alternativa de bajo riesgo mientras se decide lo anterior:** seguir operando con `v2.3.7`
tal como está hoy (sin cambios, sesión real intacta) y tratar el 463 como un riesgo conocido y
aceptado a corto plazo — ya está así en `PROJECT_STATE.md`, no requiere ninguna acción adicional.

Nuestra recomendación: intentar (A), en aislamiento total de la instancia real, antes de decidir
nada más — es, con la información que hay hoy, el único camino conocido hacia una instancia
`WHATSAPP-BAILEYS` funcional con Baileys ≥ rc.10, y con un perfil de riesgo razonable (código
público, auditado, aprobado). Antes de ejecutarlo, dado que implica construir y correr una imagen
que nosotros mismos compilamos (no una ya publicada por Evolution Foundation), preferimos
confirmarlo explícitamente con el equipo/usuario antes de proceder.
