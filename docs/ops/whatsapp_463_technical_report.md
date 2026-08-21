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

## 6. Conclusión y lo que se necesita del equipo técnico

Es una restricción del lado de los servidores de WhatsApp contra clientes no oficiales que
intentan responder a contactos nuevos/en frío, expuesta por un hueco de implementación
(persistencia/reenvío de `tctoken`/`cstoken`) presente — confirmado — en **las tres
librerías/motores no oficiales investigados** (Baileys, whatsmeow, whatsapp-web.js). No parece
ser algo que se resuelva ajustando configuración de nuestro despliegue.

Preguntas concretas para el equipo técnico:
1. ¿Conocen alguna versión de Evolution API/Baileys donde el fix de `tctoken`/`cstoken` (PRs
   #2257/#2339/#2438 de Baileys) esté realmente completo y probado contra este escenario
   exacto (responder a un contacto que nos escribió por primera vez)?
2. ¿Hay alguna otra integración/gateway de WhatsApp (fuera de Baileys/whatsmeow/whatsapp-web.js)
   con historial confirmado de **no** tener este problema?
3. ¿Vale la pena evaluar la API oficial de WhatsApp Business Cloud de Meta (de pago, requiere
   aprobación) como la única ruta con garantía real, dado que es la implementación oficial del
   protocolo?
