# Mantenimiento de Evolution API / WhatsApp — error 463 y plan de continuidad

**Última actualización:** 2026-08-21
**Para el detalle completo de la investigación (todo lo probado, con logs y evidencia):**
`docs/ops/whatsapp_463_technical_report.md`. Este documento es el resumen operativo — qué hacer,
no todo lo que se investigó para llegar aquí.

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
| **3 — Cobertura del 463** | contacto frío inicial | ✅ validado — **contactos fríos *distintos* adicionales** | ⏳ Pendiente |
| **4 — Integración real** | flujo completo WhatsApp → webhook → backend → IA → Evolution → WhatsApp | ⏳ Pendiente — ver plan abajo |
| **5 — Artefacto reproducible** | commit congelado en repo propio, Dockerfile reproducible, imagen versionada, digest registrado | ⏳ Pendiente |
| **6 — Promoción formal** | backup fresco, ensayo con BD clonada, migración real, misma instancia `amza-empaques`, QR nuevo, smoke test | ⏳ Pendiente |

**Importante:** el número real de WhatsApp está conectado hoy a la instancia de prueba (build
`45d3122`, puerto 8082, instancia `amza-empaques-pr2608-test`), **no** al backend real de la
aplicación. La capa de transporte de WhatsApp está validada parcialmente sobre el número real;
la integración con la aplicación (backend + IA) todavía no se ha probado. No es correcto decir
que "la solución ya está en producción" — el número real está conectado a una build validada,
pero el backend de la aplicación (`amza-commercial-ai-platform`) sigue apuntando a `v2.3.7`
(desconectado) en `docker-compose.yml`.

## 5. Plan para la próxima sesión

### Gate 3 — cerrar cobertura
Conseguir 1-2 contactos fríos más (distintos del ya usado) y repetir la prueba de entrega. No
hace falta repetir reinicio/reconexión/persistencia — eso ya está validado.

### Gate 4 — integración real (decisión ya tomada: Opción A)
En vez de promover primero la build al `docker-compose` real, se prueba el flujo completo end to
end apuntando temporalmente el backend real a la instancia de prueba, sin tocar la configuración
permanente de producción:

- Crear una configuración de entorno explícita de validación (ej. `.env.test-integration`, nunca
  el `.env` real) con `EVOLUTION_API_BASE_URL=http://localhost:8082` y
  `EVOLUTION_INSTANCE_NAME=amza-empaques-pr2608-test`.
- Confirmar que solo hay una URL/instancia en juego antes de arrancar el backend con esa config
  (para no correr el riesgo de que procese contra dos instancias a la vez).
- Arrancar el backend con esa config temporal, registrar el webhook de la instancia de prueba
  apuntando a él.
- Contacto real escribe → webhook → backend → IA → respuesta → Evolution test → entrega física.
- Verificar: sin duplicados, sin reenvíos de mensajes viejos, secretos/config correctos.

### Gate 5 — artefacto reproducible
Antes de promover a producción, vendorizar el código fuente del commit dentro de este repo (no
depender de que la rama del PR siga existiendo en GitHub):

```
docker/evolution/evolution-api-fix-2608/
├── .upstream/
│   ├── repository.txt       # evolution-foundation/evolution-api
│   ├── commit.txt           # 45d3122ca998b7d26b5153cb97984509e3289b92
│   └── patch-reference.txt  # PR #2608
├── Dockerfile                # con la imagen base (node:24-alpine) fijada por digest, no por tag flotante
├── source/                   # snapshot del código en ese commit
└── README.md                 # por qué existe esta copia, qué incluye
```

Registrar también, no solo el commit: el `Image ID` local de la build que se validó
(`docker inspect --format='{{.Id}}' <imagen>`), la versión exacta de Node/Alpine, Baileys, y
Prisma — el commit por sí solo no garantiza una rebuild idéntica si la imagen base `node:24-alpine`
cambia con el tiempo.

### Gate 6 — promoción formal
1. Backup fresco de Postgres + volumen de `v2.3.7` (aunque ya haya varios de hoy, uno nuevo en el
   momento del cambio).
2. Restaurar ese backup en una Postgres **clonada**, separada — nunca la real primero.
3. Levantar la nueva build contra ese clon, correr las migraciones, confirmar que el schema queda
   correcto — solo si eso pasa, repetir contra la base real.
4. Probar `scripts/register_whatsapp_instance.py` (el script real de este repo, no llamadas
   manuales a la API como se hizo durante la investigación) contra el clon, confirmando qué pasa
   con la fila `Instance` existente, configuración, webhooks y credenciales — no asumir que es
   idempotente sin probarlo.
5. Cambiar `docker-compose.yml` para construir desde `docker/evolution/evolution-api-fix-2608/`
   en vez de tirar de `evoapicloud/evolution-api:v2.3.7`. Agregar `EVOLUTION_OPERATOR_EMAIL` a
   `.env` real — **decisión pendiente:** ¿email personal (el usado en las pruebas) o uno propio
   de Amza/Stratio para la credencial de licencia permanente?
6. Reconectar con la misma instancia (`amza-empaques`) — requiere un QR nuevo, la sesión de la
   instancia de prueba no se puede transferir directamente.
7. Smoke test: repetir Gate 4 (flujo completo) ya contra el entorno real, no el temporal.

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
