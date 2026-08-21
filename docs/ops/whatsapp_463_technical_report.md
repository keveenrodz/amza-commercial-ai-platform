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

**Estado real al día de hoy: NO confirmado que Baileys `rc13` resuelva el 463.** Se demostró que
`homolog` puede arrancar y correr migraciones correctamente con el parche de Prisma, pero nunca
se llegó a probar el envío de un mensaje real — el muro de licencia lo impide. No se ha tocado la
instancia de producción (`v2.3.7`, sesión de WhatsApp real intacta) en ningún momento de esta
prueba; todo lo anterior se hizo contra un Postgres/red Docker completamente desechables.

## 6. Conclusión y lo que se necesita del equipo técnico

Es una restricción del lado de los servidores de WhatsApp contra clientes no oficiales que
intentan responder a contactos nuevos/en frío, expuesta por un hueco de implementación
(persistencia/reenvío de `tctoken`/`cstoken`) presente en **las tres librerías/motores no
oficiales investigados** (Baileys, whatsmeow, whatsapp-web.js) — pero con una precisión
importante confirmada el 21 de agosto: **ninguna versión de Evolution API que hemos podido
probar hasta ahora incluye el Baileys posterior al fix** (todas empaquetan `rc.6`-`rc.9`; el
fix llegó en `rc.10`). La única que sí lo trae (`homolog`, oficial, internamente versión
`2.4.0`) tenía un bug de empaquetado de Prisma que **ya se logró arreglar** con un
`prisma.config.ts` propio — pero justo detrás de ese arreglo apareció un segundo bloqueador,
independiente: activación de licencia obligatoria (`LICENSE_REQUIRED`, HTTP 503 en todos los
endpoints funcionales) para cualquier versión ≥ 2.4.0, gratuita pero que exige registrar un email
de operador contra el servidor de Evolution Foundation y acepta telemetría periódica obligatoria.
**Todavía no se ha logrado probar el envío de un mensaje real con Baileys ≥ rc.10** — el 463
sigue sin confirmarse resuelto ni descartado en la práctica.

Preguntas concretas para el equipo técnico:
1. ¿Alguien del equipo ya pasó por el flujo de activación de licencia de Evolution API (`≥
   2.4.0`) antes? ¿Vale la pena que nosotros lo hagamos ahora (dar un email real, aceptar la
   telemetría descrita en 5c) solo para confirmar si Baileys `rc13` sí resuelve el 463, o
   preferirían que esperemos una versión estable (no pre-release) con el fix ya integrado y sin
   depender de `homolog`?
2. ¿Conocen alguna forma de conseguir una imagen de Evolution API funcional con Baileys ≥
   `7.0.0-rc.10` que **no** dependa de `homolog` ni de este muro de licencia — build propio,
   otro tag, o un release estable más reciente que no hayamos visto?
3. ¿Hay alguna otra integración/gateway de WhatsApp (fuera de Baileys/whatsmeow/whatsapp-web.js)
   con historial confirmado de **no** tener este problema?
4. ¿Vale la pena evaluar otras alternativas de API como openWA (https://github.com/rmyndharis/OpenWA), WAHA (https://github.com/devlikeapro/waha - https://waha.devlike.pro/), Evolution API Go (https://github.com/evolution-foundation/evolution-go)?
5. Sobre `deployfybr/evolution:latest` (sugerida por un compañero): ¿alguien puede confirmar el
   repositorio fuente real detrás de esa imagen? Sin eso no es prudente correrla contra
   credenciales reales — ver sección 5b para el detalle de por qué.

## 7. Posibles soluciones — propuestas nuestras, ninguna confirmada aún

Ninguna de las siguientes se ha probado contra el escenario real (mensaje de un contacto nuevo).
Se listan en el orden en que las probaríamos, de menor a mayor costo/riesgo:

**A. Completar la activación de licencia de `homolog` en un entorno aislado y probar el 463 de
verdad, antes de decidir nada más.** Es el paso lógico siguiente a lo ya hecho en 5c: ya se
resolvió el bug de Prisma, solo falta pasar la activación (gratuita) para poder probar si Baileys
`rc13` de verdad resuelve el 463. Se haría igual que hasta ahora — Postgres/red Docker
desechables, nunca contra la sesión real — usando `EVOLUTION_OPERATOR_EMAIL` con el mismo email
que ya se usó al activar `2.4.0-rc2` (probablemente evita el flujo manual de navegador, ver 5c).
Solo si el 463 realmente se resuelve ahí, se replicaría el patch (`prisma.config.ts` + activación)
contra la instancia real. Riesgo: se vuelve a interactuar con el servidor de licencias de un
tercero (email + telemetría, ver 5c) — antes de hacerlo preferimos confirmar con el equipo que no
hay objeción.

**B. Esperar (o pedirle al equipo técnico que confirme) una versión estable de Evolution API ≥
2.4.0 que no sea un canal pre-release**, una vez que Evolution Foundation publique una release
"real" con Baileys ≥ rc.10 — evita depender de `homolog` para producción, que por definición no
tiene garantías de estabilidad. El costo es tiempo de espera, no ingeniería.

**C. Si (A) confirma que Baileys `rc13` sí resuelve el 463, evaluar migrar la instancia real de
`v2.3.7` a esa versión** (con el mismo patch de `prisma.config.ts` mientras no exista una release
estable), aceptando como parte del trade-off: la telemetría obligatoria descrita en 5c (que según
su propia documentación no incluye contenido de mensajes ni números de contacto) y la activación
de licencia por email.

**D. Si (A) NO resuelve el 463** (es decir, ni siquiera con Baileys ≥ rc.10 desaparece el
bloqueo), eso cerraría definitivamente la vía Evolution API/Baileys como arreglable con una
actualización de versión, y la alternativa de fondo pasa a ser la API oficial de WhatsApp
Business de Meta (de pago, requiere aprobación) — o revisar de nuevo whatsmeow/whatsapp-web.js
por si alguno de los dos también corrigió esto en una versión más nueva de la que se investigó en
la sección 5.

**E. Alternativa de bajo riesgo mientras se decide lo anterior:** seguir operando con `v2.3.7`
tal como está hoy (sin cambios, sesión real intacta) y tratar el 463 como un riesgo conocido y
aceptado a corto plazo — ya está así en `PROJECT_STATE.md`, no requiere ninguna acción adicional.

Nuestra recomendación, si el equipo técnico no objeta: intentar (A) primero, en aislamiento total
de la instancia real, porque es el único paso que realmente responde la pregunta que todo este
reporte viene persiguiendo — si es Baileys `rc13`, y no otra cosa, lo que resuelve el 463.
