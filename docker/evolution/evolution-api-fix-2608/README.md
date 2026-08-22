# Evolution API — build propia (fix #2608)

Copia vendorizada del código fuente de `evolution-foundation/evolution-api`, fijada en un commit
específico, para tener una imagen reproducible que **no depende de que la rama de un PR de
terceros siga existiendo en GitHub**.

## Por qué existe esta copia

`evoapicloud/evolution-api` (las imágenes oficiales publicadas en Docker Hub) no tenía, al
momento de esta investigación, ninguna versión que combinara:

1. Baileys `>= 7.0.0-rc.10` (el fix de TC token/Reachout Timelock, relacionado con el error 463
   de WhatsApp al responder a contactos nuevos).
2. Una instancia `WHATSAPP-BAILEYS` que realmente se pudiera crear (`homolog`, la única imagen
   oficial con Baileys `rc13`, tiene un bug de release que rompe `POST /instance/create`).

El commit vendorizado aquí (ver `.upstream/commit.txt`) trae ambas cosas a la vez — es un fix ya
escrito, revisado y aprobado por un mantenedor de Evolution Foundation
(`.upstream/patch-reference.txt`), solo que nunca mergeado por un problema de CI ajeno al código.

**Detalle completo de la investigación:** `docs/ops/whatsapp_463_technical_report.md` (secciones
5b en adelante). **Resumen operativo y estado de validación:**
`docs/ops/whatsapp_evolution_maintenance.md`.

## Qué contiene

- `source/` — código fuente exacto del commit en `.upstream/commit.txt`, sin `.git/` ni
  `node_modules/` (se instalan durante la build).
- `Dockerfile` (dentro de `source/`) — el `Dockerfile` real del proyecto, sin modificar excepto
  fijar la imagen base (`node:24-alpine`) por digest en vez de por tag flotante (ver abajo).

## Modificaciones locales

**Una sola:** las dos líneas `FROM node:24-alpine` del `Dockerfile` se fijaron a
`node:24-alpine@sha256:d32cdf619f63fe0471182d08996dd516c6275bb5fd31ae06e55a570bd9e1ad43`
(resuelto el 2026-08-22). Nada más se tocó.

**Reproducibilidad confirmada, no solo asumida:** se reconstruyó la imagen desde este `Dockerfile`
vendorizado (ya con el digest fijado) y el `Image ID` resultante
(`sha256:97e46ac4c09493ac6be03e7fafa901d083fb0db3829ec5f0d32353438f6d9ef4`) coincide exactamente
con el de la imagen que se validó en vivo contra el número real (Gates 1-4, ver
`docs/ops/whatsapp_evolution_maintenance.md`). Si una reconstrucción futura da un `Image ID`
distinto, algo cambió (Docker Hub no debería reetiquetar un digest ya publicado, pero vale la
pena confirmar antes de asumir que sigue siendo la misma build validada).

## Cómo reconstruir la imagen

```bash
docker build -t evolution-api:pr2608-test docker/evolution/evolution-api-fix-2608/source/
```

## Cumplimiento de licencia — resuelto (22 de agosto)

La licencia real de Evolution API (`source/LICENSE`) es Apache 2.0 **más dos condiciones
adicionales**: (a) no remover/modificar el logo ni la información de copyright en componentes de
frontend (el `manager` que se vendorizó aquí los incluye, sin tocar), y (b) **si se usa dentro de
otro sistema — incluso uno cerrado — debe mostrarse una notificación clara y visible de que se
está usando Evolution API**, accesible para los administradores del sistema.

Implementado como un texto pequeño (`text-[10px] text-ink-faint`) dentro de la tarjeta de
WhatsApp en `frontend/app/(workspace)/admin/page.tsx` (`/admin` → Canales) — visible solo para
administradores, ya que esa ruta está protegida por rol desde spec 014, no para asesores ni
clientes.

## Cuándo dejar de usar esta imagen

En cuanto [PR #2608](https://github.com/evolution-foundation/evolution-api/pull/2608) se mergee
y salga en una release oficial estable (no pre-release/`homolog`), migrar a esa versión oficial y
borrar este directorio — no tiene sentido mantener una build propia una vez que el fix es oficial.
Antes de cada actualización de Evolution API, confirmar qué versión de Baileys trae empaquetada
(no asumir que una versión más nueva automáticamente trae un Baileys más nuevo — `2.4.0-rc2` no lo
hizo).
