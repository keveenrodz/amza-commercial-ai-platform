# 013b Design System Alignment

## Propósito

Gap real encontrado por el usuario al revisar spec 013 en el navegador: la interfaz implementada
en specs 011-013 no se parece al mockup validado (`docs/design/amza_workspace_mockup/`), y la causa
no es solo de ejecución — las specs 011/012, tal como quedaron escritas, ya usaban clases Tailwind
genéricas (`bg-emerald-900`, `text-gray-500`) y el boilerplate de fuente/color de Next.js (Geist,
`--background: #ffffff`) en vez de transcribir la paleta, tipografía y layout reales que el mockup
validó con el usuario. Este spec corrige eso — es puramente visual/estructural, no agrega dominio
nuevo, y se ubica entre spec 013 y spec 014 para no seguir construyendo funcionalidad sobre una base
visual que no es la acordada.

Dos gaps distintos, corregidos juntos porque comparten causa (nunca se portó el mockup de verdad):

1. **Paleta, tipografía y tokens** — nunca se transcribieron del mockup a `globals.css`/Tailwind.
2. **Layout** — el mockup es una vista única de 3 columnas simultáneas (lista + chat + panel de
   cliente, estilo WhatsApp Web/Telegram Desktop); lo implementado son dos rutas separadas
   (`/opportunities` y `/opportunities/[id]`, cada una una página completa) heredadas de spec 009
   (anterior al mockup), nunca revisadas al escribir 011/012.

**Explícitamente fuera de alcance:**

- Ningún cambio de dominio, endpoint, caso de uso, ni comportamiento de negocio — cero cambios en
  `backend/`.
- No se reintroduce el archivo del mockup tal cual (HTML/CSS/JS con datos hardcodeados) — se portan
  sus tokens y estructura a componentes React/Tailwind idiomáticos que siguen usando React Query,
  los hooks y los endpoints reales ya construidos.
- El overlay de "soltar archivos aquí" (`.drop-overlay` del mockup) no se porta — no hay ninguna
  funcionalidad de adjuntar archivos nuevos detrás (eso es Media Library, spec futura); portar solo
  el CSS sin comportamiento sería decoración sin propósito.
- No se rediseña el contenido de los placeholders de `/knowledge-base`, `/media`, `/admin` más allá
  de recolorearlos con los tokens nuevos — su contenido real sigue siendo de sus specs futuras.

---

## 1. Design tokens — `frontend/app/globals.css`

Reemplaza los tokens genéricos (`--background`, `--foreground`) por los tokens reales del mockup,
en los mismos 3 estados de tema ya establecidos desde spec 011 (sistema por defecto vía
`prefers-color-scheme`, override explícito gana en ambas direcciones vía `data-theme`). Valores
tomados directo de `docs/design/amza_workspace_mockup/template.html` (bloque `:root` /
`@media (prefers-color-scheme: dark)` / `:root[data-theme="dark"]`):

| Token | Claro | Oscuro |
|---|---|---|
| `--paper` | `#f6f6f4` | `#14160f` |
| `--surface` | `#ffffff` | `#1b1e17` |
| `--surface-2` | `#eef0ea` | `#242820` |
| `--surface-3` | `#e3e6dc` | `#2d3226` |
| `--ink` | `#1b1d16` | `#edefe7` |
| `--ink-muted` | `#63695a` | `#98a08c` |
| `--ink-faint` | `#9aa08e` | `#626b56` |
| `--line` | `#dfe2d7` | `#333829` |
| `--accent` | `#5f7d55` | `#74ac5e` |
| `--accent-deep` | `#3a5233` | `#8fc878` |
| `--accent-soft` | `#eef1ea` | `#24331c` |
| `--warn` / `--warn-soft` | `#b5722a` / `#f4e6d6` | `#d99553` / `#3a2c1c` |
| `--info` / `--info-soft` | `#3b6c93` / `#dde9f0` | `#6fa8d9` / `#1e2c37` |
| `--whatsapp` / `--whatsapp-soft` | `#2f8f5b` / `#dcf0e4` | `#4fbf86` / `#1a3327` |
| `--gold` / `--gold-soft` | `#ad8112` / `#f6ecd2` | `#e8c158` / `#362b13` |
| `--overdue` / `--overdue-soft` | `#b3432f` / `#f5e0da` | `#e0836f` / `#3a231d` |
| `--bubble-customer` | `#ffffff` | `#242820` |
| `--bubble-agent` | `#eef2ea` | `#22301f` |
| `--bubble-advisor` | `#dfeaf4` | `#1d2a35` |
| `--focus` | `#3a5233` | `#8fc878` |

`--shadow` no es un color — es un valor de `box-shadow` de dos capas que también cambia entre
temas (opacidad más alta en oscuro). Se declara como variable propia (`--app-shadow`) junto a los
colores, mismo patrón de 3 estados:

```css
--app-shadow: 0 1px 2px rgba(27, 29, 22, 0.06), 0 8px 24px rgba(27, 29, 22, 0.06); /* claro */
--app-shadow: 0 1px 2px rgba(0, 0, 0, 0.3), 0 8px 24px rgba(0, 0, 0, 0.35); /* oscuro */
```

Mapeo a utilidades de Tailwind v4 (CSS-first, `@theme inline` — mismo mecanismo que ya usa
`globals.css` para `--color-background`/`--color-foreground`/`--font-sans`): cada token de color
gana su utilidad (`bg-paper`, `bg-surface`, `bg-surface-2`, `text-ink`, `text-ink-muted`,
`border-line`, `bg-accent`, `text-accent-deep`, `bg-warn-soft`, `text-overdue`, etc.), y
`--app-shadow` se expone como `shadow-card` (`--shadow-card: var(--app-shadow)`). Se elimina
`--color-background`/`--color-foreground` — todo el código que los usaba (`bg-foreground`,
`text-background`, login y composer) pasa a los tokens nuevos (sección 3).

`mark` (resaltado de búsqueda, spec 012) cambia de un amarillo hardcodeado a `var(--gold-soft)` /
`var(--ink)` — mismo color que ya usa el mockup para esto (`#thread mark`).

---

## 2. Tipografía — Manrope vía `next/font/google`

El mockup carga Manrope como fuente autocontenida (`@font-face` con un `data:` URI en base64)
porque es un HTML de un solo archivo sin paso de build. En Next.js, `next/font/google` logra el
mismo resultado real (cero requests externos en runtime, la fuente se auto-hospeda en build) de
forma idiomática — se reemplaza `Geist`/`Geist_Mono` (`frontend/app/layout.tsx`) por Manrope, pesos
500–800 (mismo rango que el mockup declaró), expuesta como `--font-manrope` → utilidad Tailwind
`font-heading`.

El mockup aplica Manrope como fuente heredada de todo `.chrome` (el contenedor raíz de la app), pero
como su declaración `@font-face` solo cubre el rango 500–800, cualquier texto sin peso explícito
(el cuerpo de los mensajes, párrafos sueltos, queda en 400/normal) cae fuera de ese rango y el
navegador lo renderiza con la siguiente fuente del stack (sans del sistema) — así es como el mockup
ya distingue, sin proponérselo como dos fuentes separadas, texto estructural (Manrope: nombres,
encabezados, chips, botones, etiquetas) de texto de lectura (sans del sistema: contenido de
mensajes, notas). `next/font` con pesos discretos (500/600/700/800) no reproduce ese fallback
automático — así que se replica el mismo resultado de forma explícita: la utilidad `font-heading`
se aplica puntualmente a los mismos elementos que el mockup marcaba con `font-family: 'Manrope'`
(nombres de contacto, encabezados de sección, chips, tabs, botones, labels de burbuja), dejando el
cuerpo de mensajes/notas en la fuente sans por defecto de Tailwind. Documentado aquí para que quien
lea el código no asuma que fue un olvido de aplicar `font-heading` en todas partes.

---

## 3. Rail nav — `frontend/components/workspace-shell.tsx`

Redibuja la barra lateral para que coincida con `.rail` del mockup en vez del `bg-emerald-900`
genérico actual:

- Fondo `bg-accent-deep` (no `bg-emerald-900`), ancho 72px (no 64px/`w-16`).
- Logo dentro de una tarjeta redondeada `bg-surface` con `shadow-card` (`.rail-mark`), no suelto.
- Cada botón de navegación gana un tooltip flotante a la derecha al hacer hover (`.rail-tip` del
  mockup: fondo `bg-ink`, texto `text-paper`, oculto por defecto, visible en `:hover` — se puede
  hacer con Tailwind puro, `opacity-0 group-hover:opacity-100`, sin JS adicional).
- El encabezado superior actual (`Kevin R. (advisor)` + "Cerrar sesión" en una barra horizontal
  separada) **no existe en el mockup** — se reemplaza por el patrón real: un avatar circular con
  iniciales al final del rail (`.rail-avatar`, mismo componente `initials()` ya usado en
  `status-chips.tsx`) con un `title` nativo (`"{nombre} — {rol}"`) para accesibilidad básica, que al
  hacer clic abre un menú flotante pequeño (mismo patrón de cierre en fase de captura ya establecido
  — ver memoria de decisiones técnicas) con el nombre completo, el rol, y "Cerrar sesión". El
  toggle de tema (`ThemeToggle`, ya construido en spec 011) se recolorea pero mantiene su lugar
  justo arriba del avatar, como en `.rail-foot`.
- Esto es una pérdida de visibilidad permanente del nombre (antes siempre en pantalla, ahora detrás
  de un clic/hover) a cambio de fidelidad real con el mockup — aceptado porque el mockup es la
  referencia validada con el usuario, y el nombre/rol se sigue pudiendo confirmar en un clic.

---

## 4. Recoloreo de componentes existentes

Sin tocar lógica/estado/hooks de ningún archivo — solo clases. Cambios puntuales por archivo:

- **`chat-bubble.tsx`**: burbujas usan `bg-bubble-customer`/`bg-bubble-agent`/`bg-bubble-advisor`
  (no `bg-white`/`bg-sky-100`/`bg-emerald-100`); `shadow-card`; label de burbuja en `font-heading`
  `text-info` (asesor e IA comparten color de label en el mockup — `.row.out .bubble.agent
  .bubble-label` y `.bubble.advisor .bubble-label` son ambos `var(--info)`); nota de sistema en
  `bg-surface-2 text-ink-muted`.
- **`message-composer.tsx`**: botón de enviar `bg-accent hover:bg-accent-deep` (no
  `bg-foreground`/`text-background`); textarea con `border-line bg-paper focus:border-accent`
  (mismo estilo que `.composer textarea` del mockup).
- **`file-card.tsx`**: ícono en `bg-accent-soft text-accent-deep` (no `bg-emerald-100`).
- **`emoji-picker.tsx`**: contenedor `bg-surface border-line shadow-card`; fondo de búsqueda
  `bg-surface-2`; hover de emoji `hover:bg-surface-2`; encabezado "Frecuentes"
  `text-ink-faint font-heading`.
- **`status-chips.tsx`**: recolorea `ChannelChip` (`.chip.wa`/`.chip.tg` → `bg-whatsapp-soft
  text-whatsapp` / `bg-info-soft text-info`), `StatusChip` (IA → `bg-info-soft text-info`; Mía →
  `bg-accent-soft text-accent-deep`; Asignada → `bg-surface-2 text-ink`), `FollowUpChip`
  (`bg-warn-soft text-warn` / vencido `bg-overdue-soft text-overdue`, igual que `.chip.followup`
  del mockup).
- **`contact-panel.tsx`**: fondo `bg-surface`; secciones con encabezados `font-heading text-ink-faint
  uppercase`; `tag-pill` en `bg-accent-soft text-accent-deep`; tarjeta de seguimiento
  `bg-warn-soft`/`bg-overdue-soft` (igual que `.followup-card`); notas en `bg-surface-2`.
- **`date-time-picker.tsx`**: contenedor `bg-surface border-line shadow-card`; día de hoy
  `text-accent-deep font-bold`; día deshabilitado `text-ink-faint opacity-45`; botón "Listo"
  `bg-accent text-white`; AM/PM activo `bg-accent text-white`.
- **`opportunities/page.tsx`** y **`opportunities/[id]/page.tsx`**: ver sección 5 (se reestructuran,
  no solo se recolorean).
- **`login/page.tsx`**, **`admin/page.tsx`**, **`knowledge-base/page.tsx`**, **`media/page.tsx`**:
  recoloreo directo (`bg-accent`/`text-white` en vez de `bg-foreground`/`text-background`;
  `bg-accent-soft text-accent-deep` en vez de `bg-emerald-100 text-emerald-900` para el badge
  "Próxima spec"; `text-ink-muted` en vez de `text-gray-500`).

---

## 5. Layout unificado de 3 columnas

El mockup mantiene lista + chat + panel de cliente visibles **a la vez**; hoy son dos páginas
completas que se reemplazan una a la otra al navegar. Se resuelve sin romper el principio ya
frozen de spec 011 ("cada sección es una ruta real, nunca un `if` de JavaScript decidiendo qué
mostrar") usando *layouts anidados* de Next.js — mecanismo diseñado exactamente para esto:

`frontend/app/(workspace)/opportunities/layout.tsx` (nuevo) — Client Component que:

- Contiene toda la lógica que hoy vive en `opportunities/page.tsx`: tabs, buscador, orden/filtros,
  y el renderizado de la columna de lista completa (sección `.list-col` del mockup).
- Recibe `children` y los renderiza en el espacio de chat+panel de cliente, a la derecha de la
  lista — `children` es `opportunities/page.tsx` cuando la URL es `/opportunities` (sin selección)
  o `opportunities/[id]/page.tsx` cuando hay una conversación abierta.
- Usa `useParams<{ id?: string }>()` (hook de cliente, no requiere que el layout reciba el param
  por props) para saber qué fila resaltar como `.convo.selected` — funciona porque Next.js resuelve
  los params de la ruta completa sin importar en qué layout/página se llama el hook.
- Este layout se monta una sola vez por navegación entre `/opportunities` y `/opportunities/[id]`
  (son hermanos bajo el mismo layout) — la lista **no se remonta** al abrir/cerrar una conversación,
  a diferencia de hoy. Efecto secundario positivo: el estado de tabs/búsqueda/filtros sobrevive la
  navegación, algo que hoy se pierde.

`opportunities/page.tsx` (reescrito, mucho más corto) — pasa a ser el estado vacío del mockup
(`.placeholder-panel`: ícono, "Selecciona una conversación para comenzar", texto de apoyo),
mostrado cuando no hay ninguna oportunidad abierta en `/opportunities/[id]`.

`opportunities/[id]/page.tsx` — conserva toda su lógica (ya construida en spec 013: panel de
cliente, reasignar, no-leído, seguimiento), solo dejando de renderizar el link "← Volver" (ya no
hace falta, la lista sigue visible a la izquierda todo el tiempo) y de envolver todo en su propio
layout de página completa (ahora es contenido dentro del layout de `opportunities/`).

---

## 6. Tests

- Frontend e2e (`frontend/tests/e2e/advisor-workspace.spec.ts`): varios tests navegan a
  `/opportunities/opp-mine` esperando que sea una página aislada — se ajustan para el nuevo layout
  compartido (la lista sigue montada y visible; "← Volver" ya no existe, se quita esa aserción si
  alguna la usaba). Los conteos de `getByRole("link")` dentro de `<main>` pueden cambiar si el
  layout introduce elementos nuevos con rol `link`/`button` — se revisan uno por uno, no se asume.
- Sin tests de backend nuevos — este spec no toca `backend/`.

---

## Próximo paso

Con la base visual alineada al mockup, sigue spec 014 (**Admin Governance & Access Control**), como
ya estaba planeado antes de este spec correctivo.
