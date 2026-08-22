# Mantenimiento de Evolution API / WhatsApp — error 463 y plan de continuidad

**Última actualización:** 2026-08-22
**Para el detalle completo de la investigación (todo lo probado, con logs y evidencia):**
`docs/ops/whatsapp_463_technical_report.md`. Este documento es el resumen operativo — qué hacer,
no todo lo que se investigó para llegar aquí.

## 0. Estado exacto de la infraestructura en este momento (para retomar sin contexto previo)

**Producción real ya está en la build validada, conectada y funcionando.** Esto es lo que existe
en la máquina real (verificado 2026-08-22, después de completar el núcleo de Gate 6) — nada de
esto vive en memoria de conversación:

- **`amza-commercial-ai-platform-evolution-api-1`** — ya **no** es la imagen oficial `v2.3.7`.
  `docker-compose.yml` ahora la construye (`build:`) desde
  `docker/evolution/evolution-api-fix-2608/source/` (el commit del PR #2608, Baileys `rc13`).
  Puerto `8080`, instancia `amza-empaques`, **conectada al número real
  (+57 301 509 2386, `connectionStatus: open`)**, con licencia auto-activada desde un registro ya
  persistido en la base de datos real (tabla `RuntimeConfig`, de una activación anterior con
  `keveenrodriguez@gmail.com`). Su Postgres es la misma de siempre
  (`amza-commercial-ai-platform-evolution-postgres-1`), ya migrada a este build, datos intactos
  (más un backup fresco pre-cambio en `backups/evolution_db_backup_pre_gate6_*.sql`).
- **Backend local** (`python main.py`, fuera de Docker) corriendo **con su `.env` normal, sin
  overrides** — apunta correctamente a `http://localhost:8080`/`amza-empaques`, la instancia real.
  `EVOLUTION_OPERATOR_EMAIL=keveenrodriguez@gmail.com` ya está en `.env`/`.env.example`.
- **Webhook de producción** apunta a `http://172.26.0.1:8000/webhooks/whatsapp/amza-empaques` —
  `172.26.0.1` es el gateway de la red `amza-commercial-ai-platform_default`, así el contenedor
  alcanza el backend que corre directo en el host (no hay un contenedor `backend` corriendo en
  esta máquina — si eso cambia, hay que actualizar el webhook a `http://backend:8000/...` en su
  lugar, el nombre del servicio en `docker-compose.yml`).
- **La instancia de prueba** (`evo-pr2608-test-api`/`amza-empaques-pr2608-test`, puerto `8082`)
  fue desconectada (`DELETE /instance/logout/...`) tras un bug real de mensajes duplicados
  causado por tenerla conectada en paralelo a producción (ver Gate 6, punto 7), y **ya se
  eliminó por completo** (`docker rm`, junto con su Postgres y red dedicadas) — no queda nada de
  esa infraestructura corriendo, el commit vendorizado en el repo es suficiente para reconstruirla
  si algún día hace falta.
- **Código fuente vendorizado**, ya en el repo (no depende de un directorio temporal ni de que
  GitHub siga teniendo la rama del PR): `docker/evolution/evolution-api-fix-2608/`.
- **Backups en `backups/`** (no en git, `.gitignore`): varios timestamps, el más reciente
  (`pre_gate6_*`) es de justo antes de este cambio.
- **Pendiente real, no técnico:** la notificación de uso de Evolution API que exige su licencia
  (ver Gate 5/6 más abajo) — no bloquea el funcionamiento, pero no está resuelto.

## 1. El problema, en una frase

Evolution API/Baileys (WhatsApp no oficial) rechazaba en silencio (`status 0`,
`messageStubParameters: ["463"]`) cualquier respuesta automática a un contacto que le escribía
por primera vez a la cuenta de WhatsApp Business — inutilizando el canal para el caso de uso real
del piloto (cliente nuevo escribiendo por primera vez).

## 2. Causa raíz confirmada

Dos causas independientes, ambas confirmadas con evidencia real, no teoría:

1. **Versión de Baileys.** El manejo correcto de `tctoken`/Reachout Timelock (el mecanismo que
   WhatsApp exige para no tratar la respuesta como espam a un contacto "en frío") se agregó en
   Baileys `7.0.0-rc.10`. `v2.3.7` (la versión en producción hasta este cambio) empaqueta
   `7.0.0-rc.9` — la versión inmediatamente anterior al fix.
2. **Bug de empaquetado en Evolution API**, independiente del 463: `POST /instance/create`
   fallaba siempre por un filtro de sanitización mal aplicado también a esa ruta — ya reportado
   públicamente como [issue #2631](https://github.com/evolution-foundation/evolution-api/issues/2631)
   y con fix escrito, revisado y aprobado por un mantenedor en
   [PR #2608](https://github.com/evolution-foundation/evolution-api/pull/2608) — nunca mergeado
   por un problema de CI ajeno al código.

## 3. Solución encontrada y validada (parcialmente)

Se construyó una imagen Docker propia desde el commit exacto del PR #2608
(`45d3122ca998b7d26b5153cb97984509e3289b92`), que trae **a la vez** el fix de creación de
instancia y Baileys `7.0.0-rc13`. Probada contra el número real de negocio (+57 301 509 2386, con
autorización explícita): **primera entrega real confirmada a un contacto frío en toda la
investigación**, sostenida en tres intercambios distintos con el mismo contacto (incluyendo
conversación orgánica real, no solo mensajes de prueba).

## 4. Estado de validación — estructura de gates

| Gate | Contenido | Estado |
|---|---|---|
| **1 — Transporte básico** | creación de instancia, QR, conexión, `sendText`, entrega física | ✅ Completo |
| **2 — Estabilidad de sesión** | reinicio del contenedor, reconexión, persistencia de sesión | ✅ Completo |
| **3 — Cobertura del 463** | 2 contactos fríos distintos, ambos con entrega real confirmada | ✅ Completo |
| **4 — Integración real** | flujo completo WhatsApp → webhook → backend → IA → Evolution → WhatsApp | ✅ Completo (22 de agosto) |
| **5 — Artefacto reproducible** | commit congelado en repo propio, Dockerfile reproducible, imagen versionada, digest registrado | ✅ Completo (22 de agosto) |
| **6 — Promoción formal** | backup fresco, ensayo con BD clonada, migración real, misma instancia `amza-empaques`, QR nuevo, smoke test | ✅ Núcleo completo (22 de agosto) — falta solo el pendiente de licencia (no bloqueante) |

**Importante:** el número real de WhatsApp está conectado hoy a la instancia de prueba (build
`45d3122`, puerto 8082, instancia `amza-empaques-pr2608-test`), **no** al backend real de la
aplicación. La capa de transporte de WhatsApp está validada parcialmente sobre el número real;
la integración con la aplicación (backend + IA) todavía no se ha probado. No es correcto decir
que "la solución ya está en producción" — el número real está conectado a una build validada,
pero el backend de la aplicación (`amza-commercial-ai-platform`) sigue apuntando a `v2.3.7`
(desconectado) en `docker-compose.yml`.

## 5. Plan para la próxima sesión

### Gate 3 — cerrado (21 de agosto)
Un segundo contacto frío, genuinamente distinto (número diferente, nunca había escrito antes)
escribió y se le respondió — entrega confirmada por el receptor, sin 463 en los logs. Con dos
contactos distintos validados (más las tres rondas ya hechas sobre el primero: mensaje inicial,
reinicio/reconexión, conversación orgánica), Gate 3 se considera cerrado. No hace falta seguir
sumando contactos solo por acumular conteo — el siguiente trabajo de valor real es Gate 4.

### Gate 4 — cerrado (22 de agosto)
Se ejecutó la Opción A tal como estaba planeada, sin tocar el `.env` real: variables
`EVOLUTION_API_BASE_URL`/`EVOLUTION_API_KEY`/`EVOLUTION_INSTANCE_NAME` exportadas como variables
de entorno reales antes de arrancar `python main.py` (pydantic-settings les da prioridad sobre el
`.env` file, así que no hizo falta ni siquiera crear un archivo `.env.test-integration` separado
— alcanzó con exportarlas en el shell). Se reinició el proceso de backend local existente (venía
corriendo desde una sesión anterior, apuntando a `v2.3.7`) con estas variables.

Se registró el webhook en la instancia de prueba (`POST /webhook/set/amza-empaques-pr2608-test`)
apuntando a `http://172.19.0.1:8000/webhooks/whatsapp/amza-empaques` — `172.19.0.1` es el gateway
de la red Docker del contenedor de prueba, que en Linux permite alcanzar servicios corriendo
directamente en el host (el backend, corrido con `python main.py`, no en un contenedor).

**Resultado: flujo completo confirmado, sin ninguna intervención manual.** Un mensaje real
("Hola, que empaque tienen para perros y hamburguesas?") llegó por webhook (`200`, verificación
de `X-Webhook-Secret` correcta — confirma que Evolution API sí reenvía headers personalizados de
webhook, algo que spec 016 había dejado como no confirmado), el backend generó una respuesta real
vía OpenRouter, aplicó el delay de anti-baneo del worker, y la envió
(`POST /message/sendText → 201`). **La persona confirmó que la respuesta le llegó a su
teléfono.** Sin mensajes duplicados verificado en la base de datos después. Esta es la primera
vez que se prueba el pipeline completo de la aplicación (no solo el transporte de WhatsApp)
contra Baileys `rc13` — cierra Gate 4.

**Estado al momento de escribir esto:** el proceso de backend sigue corriendo con la
configuración temporal (apuntando a `:8082`/`amza-empaques-pr2608-test`), no con el `.env` real.
Antes de volver a trabajo normal de desarrollo, hay que reiniciarlo sin esas variables de entorno
exportadas para que vuelva a leer la configuración real del `.env`.

### Gate 5 — cerrado (22 de agosto)
Vendorizado en `docker/evolution/evolution-api-fix-2608/`:

```
docker/evolution/evolution-api-fix-2608/
├── .upstream/
│   ├── repository.txt       # evolution-foundation/evolution-api
│   ├── commit.txt           # 45d3122ca998b7d26b5153cb97984509e3289b92
│   └── patch-reference.txt  # PR #2608, estado, por qué este commit específico
├── source/                   # snapshot completo del código en ese commit, sin .git ni node_modules
│   └── Dockerfile            # con node:24-alpine fijado por digest en las dos etapas (builder y final)
└── README.md                 # por qué existe esta copia, limitaciones, cuándo retirarla
```

**Reproducibilidad confirmada, no solo asumida:** se reconstruyó la imagen desde este Dockerfile
vendorizado y el `Image ID` resultante
(`sha256:97e46ac4c09493ac6be03e7fafa901d083fb0db3829ec5f0d32353438f6d9ef4`) coincide exactamente
con el de la imagen ya validada en vivo (Gates 1-4). Digest de `node:24-alpine` fijado:
`sha256:d32cdf619f63fe0471182d08996dd516c6275bb5fd31ae06e55a570bd9e1ad43`.

**Hallazgo no técnico, pendiente:** la licencia real de Evolution API (Apache 2.0 + condiciones
adicionales) exige mostrar una notificación visible de que se usa Evolution API cuando se integra
dentro de otro sistema, accesible para administradores. No implementado todavía — ver
`docker/evolution/evolution-api-fix-2608/README.md` para el detalle. Hay que resolverlo antes de
considerar esto completamente cerrado para producción real, no es opcional.

### Gate 6 — núcleo cerrado (22 de agosto), un pendiente de cumplimiento abierto

1. **Backup fresco** de Postgres + volumen de producción — hecho
   (`backups/evolution_db_backup_pre_gate6_*.sql`).
2. **Restaurado en una Postgres clonada**, separada de la real — hecho.
3. **Migración probada contra el clon primero:** `Migration succeeded`, sin conflictos. El clon
   reveló algo importante: **la licencia ya estaba persistida en la base de datos real**
   (tabla `RuntimeConfig`, de una activación anterior con el mismo email) — se activa sola al
   arrancar, sin necesitar `EVOLUTION_OPERATOR_EMAIL` de nuevo. Solo entonces se repitió contra
   la base real — mismo resultado, limpio.
4. **`scripts/register_whatsapp_instance.py` NO es idempotente — confirmado, no asumido.**
   Probado contra el clon: `POST /instance/create` con el nombre `amza-empaques` (ya existente)
   responde `403 "This name ... is already in use."`. El procedimiento correcto para reconectar
   una instancia existente es `GET /instance/connect/{name}` (QR nuevo) — nunca volver a correr
   ese script contra una instancia que ya existe.
5. **`docker-compose.yml` actualizado** — el servicio `evolution-api` ahora hace `build:` desde
   `docker/evolution/evolution-api-fix-2608/source/` en vez de `image: evoapicloud/evolution-api:v2.3.7`.
   `EVOLUTION_OPERATOR_EMAIL` agregado a `.env`/`.env.example` con
   `keveenrodriguez@gmail.com` (decisión del usuario: mismo email de las pruebas).
6. **Reconectado con QR nuevo, desde la app real** (`/admin` → Canales → Conectar) — no con
   scripts manuales. Mismo nombre de instancia (`amza-empaques`), sesión de WhatsApp verificada
   como `open` contra el número real.
7. **Smoke test (Gate 4 contra el entorno real) — reveló un bug real de duplicados, ya
   corregido en su causa raíz.** Un mensaje del contacto se procesó **dos veces**, generando
   **dos respuestas distintas de la IA** enviadas al mismo contacto — confirmado en la base de
   datos de la app (`backend/data/amza.db`, dos filas de `messages` para el mismo texto entrante,
   27 segundos aparte). Causa: la instancia de prueba (`amza-empaques-pr2608-test`) seguía
   conectada como dispositivo vinculado adicional al mismo número, con su webhook de Gate 4
   todavía activo — WhatsApp multi-dispositivo sincronizó el mensaje a ambos dispositivos, cada
   uno disparó su propio webhook, y el backend procesó cada uno de forma independiente. **No es
   un defecto de la build nueva** — es un artefacto de nuestra propia metodología de prueba.
   Corregido desactivando el webhook de la instancia de prueba y cerrando su sesión
   (`DELETE /instance/logout/amza-empaques-pr2608-test`) — confirmado después que solo queda una
   instancia conectada (`amza-empaques`, producción).

   **Hallazgo de robustez real, para el backlog — no bloquea el cierre de este gate:** el backend
   no tiene ninguna protección contra procesar el mismo mensaje de WhatsApp dos veces si llega
   por dos rutas distintas (dos webhooks, dos "instancias" viéndolo). En operación normal (una
   sola instancia conectada) no debería repetirse, pero sería razonable agregar una
   deduplicación por ID de mensaje de WhatsApp en `ReceiveIncomingMessageUseCase` como
   endurecimiento futuro, no como blocker de esta promoción.

8. **Pendiente, no resuelto — cumplimiento de licencia:** la notificación visible de uso de
   Evolution API que exige su licencia (ver sección 5, Gate 5) sigue sin implementarse. No
   bloquea el funcionamiento técnico, pero es un pendiente real, no opcional.

## 6. Qué hacer cuando Evolution API se actualice (mantenimiento futuro)

- **Antes de actualizar de versión otra vez:** confirmar qué versión de Baileys trae la nueva
  imagen (`docker run --rm --entrypoint sh <imagen> -c "cat package.json | grep baileys"`, de
  solo lectura) — no asumir que una versión más nueva de Evolution API automáticamente incluye
  un Baileys más nuevo (`2.4.0-rc2` no lo hizo).
- **Revisar si [PR #2608](https://github.com/evolution-foundation/evolution-api/pull/2608) ya se
  mergeó.** Si ya está en un release oficial estable, migrar a esa versión oficial y retirar la
  imagen vendorizada de `docker/evolution/evolution-api-fix-2608/` — deja de tener sentido mantener
  una build propia si el fix ya es oficial.
- **Si se necesita actualizar la imagen vendorizada a un commit más nuevo:** repetir el mismo
  proceso de validación completo (gates 1-4) antes de promoverla — no asumir que porque el commit
  anterior funcionó, cualquier commit posterior también lo hará.
- **La activación de licencia es por email, no por instancia.** Si se reconstruye la imagen o se
  reinstala desde cero, `EVOLUTION_OPERATOR_EMAIL` con el mismo email ya usado debería reactivar
  sin pasar por el flujo manual de navegador (confirmado empíricamente esta sesión).
