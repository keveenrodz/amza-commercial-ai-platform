# Mantenimiento de Evolution API / WhatsApp — error 463 y plan de continuidad

**Última actualización:** 2026-08-22
**Para el detalle completo de la investigación (todo lo probado, con logs y evidencia):**
`docs/ops/whatsapp_463_technical_report.md`. Este documento es el resumen operativo — qué hacer,
no todo lo que se investigó para llegar aquí.

## 0. Estado exacto de la infraestructura en este momento (para retomar sin contexto previo)

Si esta sesión se corta, esto es lo que existe en la máquina real (`docker ps -a`, verificado
2026-08-22) — nada de esto vive en memoria de conversación ni en un directorio temporal que se
borre solo:

- **`evo-pr2608-test-api`** (contenedor, imagen local `evolution-api:pr2608-test`, puerto
  `8082→8080`) — la instancia de Evolution API construida desde el commit del PR #2608, **con el
  número real de WhatsApp (+57 301 509 2386) conectado y funcionando**. Nombre de la instancia
  dentro de Evolution: `amza-empaques-pr2608-test`. **No eliminar este contenedor** — la sesión de
  WhatsApp (claves de multi-dispositivo) vive en su capa de escritura, no en un volumen aparte;
  `docker rm` la perdería. `docker stop`/`docker start` sí es seguro.
- **API key de licencia de esta instancia de prueba:**
  `e880abbe1011e87c43fffc2faa347d9853a956ac74c8ce2b1bfd29406fc7e04f` (activada contra
  `license.evolutionfoundation.com.br` con `EVOLUTION_OPERATOR_EMAIL=keveenrodriguez@gmail.com`,
  tier `community`, `customer_id: 14299`). Se usa como header `apikey` en las llamadas a
  `http://localhost:8082`.
- **`evo-pr2608-test-pg`** (contenedor, `postgres:15`) — Postgres dedicada a la instancia de
  prueba, red `evo-pr2608-test-net` (gateway `172.19.0.1`, esa IP es cómo el contenedor alcanza
  servicios corriendo directo en el host).
- **`amza-commercial-ai-platform-evolution-api-1`** (`v2.3.7`, puerto `8080`) — la instancia de
  producción real, **actualmente desconectada de WhatsApp**
  (`connectionStatus: close`, `disconnectionReasonCode: 401`) desde que se escaneó el QR de la
  instancia de prueba con el mismo número. Su Postgres (`amza-commercial-ai-platform-evolution-postgres-1`)
  sigue arriba, datos intactos.
- **Backend local** (`python main.py`, fuera de Docker) corriendo con variables de entorno
  temporales que sobreescriben el `.env` real:
  `EVOLUTION_API_BASE_URL=http://localhost:8082`,
  `EVOLUTION_API_KEY=e880abbe1011e87c43fffc2faa347d9853a956ac74c8ce2b1bfd29406fc7e04f`,
  `EVOLUTION_INSTANCE_NAME=amza-empaques-pr2608-test` — es decir, **el backend real está
  respondiendo a WhatsApp en este momento a través de la instancia de prueba, no de la de
  producción.** El webhook de la instancia de prueba está registrado apuntando a
  `http://172.19.0.1:8000/webhooks/whatsapp/amza-empaques`.
- **Código fuente de la build de prueba:** clonado en un directorio temporal de esta sesión (no
  persiste) desde `evolution-foundation/evolution-api`, commit
  `45d3122ca998b7d26b5153cb97984509e3289b92`. La imagen Docker (`evolution-api:pr2608-test`) sí
  persiste en el Docker local aunque el clon del código se pierda — pero para Gate 5 hay que
  volver a clonar ese commit y vendorizarlo en el repo (ver sección 5, Gate 5).
- **Backups tomados hoy**, en `backups/` (no en git, `.gitignore`): dumps de Postgres de
  producción y del volumen `evolution_instances` con timestamp `pre_homolog_test` y anteriores —
  todos de antes de tocar nada de esto, disponibles para restaurar si algo sale mal.

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
| **6 — Promoción formal** | backup fresco, ensayo con BD clonada, migración real, misma instancia `amza-empaques`, QR nuevo, smoke test | ⏳ Pendiente |

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

### Gate 6 — promoción formal (siguiente, en curso)
1. Backup fresco de Postgres + volumen de `v2.3.7` (aunque ya haya varios de hoy, uno nuevo en el
   momento del cambio).
2. Restaurar ese backup en una Postgres **clonada**, separada — nunca la real primero.
3. Levantar la nueva build contra ese clon, correr las migraciones, confirmar que el schema queda
   correcto — solo si eso pasa, repetir contra la base real.
4. Probar `scripts/register_whatsapp_instance.py` (el script real de este repo, no llamadas
   manuales a la API como se hizo durante la investigación) contra el clon, confirmando qué pasa
   con la fila `Instance` existente, configuración, webhooks y credenciales — no asumir que es
   idempotente sin probarlo.
5. Cambiar `docker-compose.yml` para construir desde
   `docker/evolution/evolution-api-fix-2608/source/` en vez de tirar de
   `evoapicloud/evolution-api:v2.3.7`. Agregar `EVOLUTION_OPERATOR_EMAIL` a `.env` real —
   **decisión pendiente:** ¿email personal (el usado en las pruebas) o uno propio de Amza/Stratio
   para la credencial de licencia permanente?
6. Reconectar con la misma instancia (`amza-empaques`) — requiere un QR nuevo, la sesión de la
   instancia de prueba no se puede transferir directamente.
7. Smoke test: repetir Gate 4 (flujo completo) ya contra el entorno real, no el temporal — y
   revertir el backend a su `.env` normal (sin los overrides usados para Gate 4) una vez que
   apunte de nuevo a la instancia real.
8. Resolver el pendiente de licencia (notificación visible de uso de Evolution API) antes de
   considerar esto cerrado del todo.

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
