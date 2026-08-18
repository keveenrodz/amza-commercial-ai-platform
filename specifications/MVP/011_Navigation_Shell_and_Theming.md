# 011 Navigation Shell & Theming

## Propósito

Primer paso del rediseño de interfaz acordado antes de retomar el piloto operativo con Amza
Empaques: completar más la plataforma en vez de pilotear la versión actual (decisión registrada en
`PROJECT_STATE.md`). El rediseño se validó primero como mockup interactivo, sin backend
(`docs/design/amza_workspace_mockup/`, revisado y ajustado varias veces con retroalimentación
directa antes de comprometerlo a código real) — este spec implementa, en `frontend/` de verdad, la
primera pieza de esa validación: el **contenedor**, no el contenido.

Barra lateral de navegación, logo de marca, y tema claro/oscuro persistente, envolviendo las
páginas que ya existen (`/opportunities`, `/opportunities/[id]`, specs 007-010) sin tocar su lógica
de negocio, sus datos, ni su diseño interno.

**Explícitamente fuera de alcance** (no es "todavía no" — es una decisión de alcance, cada ítem
tiene su propio spec numerado ya acordado):

- Rediseño del panel de chat/mensajes estilo WhatsApp Web, panel de información del cliente
  (etiquetas, notas, seguimiento), emojis, adjuntos — spec 012.
- Contenido real de Base de conocimiento, Multimedia y Administración — specs 013 a 018. Aquí solo
  existen como rutas placeholder ("Próximamente").
- Cualquier endpoint, caso de uso, o modelo de dominio nuevo — este spec es 100% frontend.

---

## Alcance — solo shell, ninguna regla de negocio nueva

Nada aquí toca `app/api/`, `core/`, `infrastructure/` ni `modules/*` del backend. Las páginas
`/opportunities` y `/opportunities/[id]` mantienen exactamente los mismos hooks que ya tienen
(`useOpportunities`, `useCurrentUser`, `useRequireAuth`, `useLogout`, `useSendMessage`, etc.) — solo
cambia **dónde** se renderizan (dentro del shell, no en un `<main>` suelto) y **qué chrome dejan de
dibujar ellas mismas** porque el shell ya lo hace (el header con nombre de usuario + "Cerrar
sesión", hoy duplicado dentro de `opportunities/page.tsx`).

---

## 1. Grupo de rutas `(workspace)`

Next.js App Router: un [route group](https://nextjs.org/docs/app/building-your-application/routing/route-groups)
no agrega segmento a la URL, solo agrupa páginas bajo un `layout.tsx` compartido. `/login` queda
**fuera** del grupo — no debe mostrar la barra lateral (nadie autenticado todavía en esa página).

```
frontend/app/
├── layout.tsx                     # cambio menor (sección 4) — sin cambio de fondo
├── page.tsx                       # sin cambios — redirige a /opportunities
├── login/
│   └── page.tsx                   # sin cambios — sigue sin shell
└── (workspace)/
    ├── layout.tsx                  # NUEVO — gating + <WorkspaceShell>
    ├── opportunities/
    │   ├── page.tsx                # MOVIDO — header duplicado eliminado (sección 2)
    │   └── [id]/
    │       └── page.tsx            # MOVIDO — sin cambios de contenido
    ├── knowledge-base/
    │   └── page.tsx                # NUEVO — placeholder "Próximamente"
    ├── media/
    │   └── page.tsx                # NUEVO — placeholder "Próximamente"
    └── admin/
        └── page.tsx                # NUEVO — placeholder "Próximamente"
```

Mover `opportunities/` y `opportunities/[id]/` es un `git mv`, no una reescritura — el Router
resuelve la misma URL (`/opportunities`, `/opportunities/[id]`) sin importar el route group que la
contenga.

---

## 2. `app/(workspace)/layout.tsx` — gating centralizado + shell

Hoy `useRequireAuth()` se llama por separado en cada página protegida — decisión explícita de spec
009 (sección 5) de no usar middleware de Next.js. Con un layout compartido para todo el grupo, tiene
sentido dejar de duplicarlo por página y llamarlo una sola vez aquí — **sigue sin ser middleware**,
solo cambia el componente que lo invoca:

```tsx
"use client";

import { useRequireAuth } from "@/hooks/use-require-auth";
import { WorkspaceShell } from "@/components/workspace-shell";

export default function WorkspaceLayout({ children }: { children: React.ReactNode }) {
  const { data: currentUser, isLoading } = useRequireAuth();

  if (isLoading || !currentUser) {
    return <p className="p-8">Cargando...</p>;
  }

  return <WorkspaceShell currentUser={currentUser}>{children}</WorkspaceShell>;
}
```

`opportunities/page.tsx` deja de llamar `useRequireAuth()` y de dibujar su propio `<header>` — el
nombre del usuario y "Cerrar sesión" ya los muestra `WorkspaceShell`. `opportunities/[id]/page.tsx`
puede seguir leyendo `useCurrentUser()` directo si necesita `currentUser.id`/`organization_slug`
para sus propias mutaciones (`useSendMessage`, etc.) — eso no es gating, es lectura de una query ya
cacheada por react-query (misma query key, sin refetch adicional; `useRequireAuth` y
`useCurrentUser` comparten caché).

---

## 3. `WorkspaceShell` — barra lateral

`frontend/components/workspace-shell.tsx` (nuevo — `frontend/components/` existe hoy vacío salvo
`.gitkeep`):

- Marca de Amza arriba (`amza-logo.png`, copiado a `frontend/public/amza-logo.png`, sección 6).
- Cuatro ítems de navegación como `<Link>` reales — **no** estado de React cambiando de sección,
  cada uno ya es su propia ruta desde la sección 1: Conversaciones (`/opportunities`), Base de
  conocimiento (`/knowledge-base`), Multimedia (`/media`), Administración (`/admin`). El activo se
  resalta con `usePathname()`.
- Nombre + rol del usuario y botón "Cerrar sesión" (`useLogout()`) — el mismo bloque que hoy vive
  duplicado dentro de `opportunities/page.tsx` (ver diff de esa página en la sección 2).
- Toggle de tema al fondo de la barra (sección 4).

Sin librería de íconos nueva — `lucide-react` u otra no está instalada hoy, y cuatro SVGs a mano
(ya dibujados y validados visualmente en el mockup) no justifican sumar una dependencia.

```tsx
"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { AdminIcon, BookIcon, ChatIcon, MediaIcon } from "@/components/icons";
import { ThemeToggle } from "@/components/theme-toggle";
import { useLogout } from "@/hooks/use-logout";
import type { CurrentUser } from "@/types/api";

const NAV_ITEMS = [
  { href: "/opportunities", label: "Conversaciones", Icon: ChatIcon },
  { href: "/knowledge-base", label: "Base de conocimiento", Icon: BookIcon },
  { href: "/media", label: "Multimedia", Icon: MediaIcon },
  { href: "/admin", label: "Administración", Icon: AdminIcon },
] as const;

export function WorkspaceShell({
  currentUser,
  children,
}: {
  currentUser: CurrentUser;
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const logout = useLogout();

  return (
    <div className="flex h-screen">
      <nav className="flex w-16 flex-shrink-0 flex-col items-center gap-2 bg-emerald-900 py-4">
        <Image
          src="/amza-logo.png"
          alt="Amza"
          width={32}
          height={32}
          className="mb-4 rounded bg-white p-1"
        />
        {NAV_ITEMS.map(({ href, label, Icon }) => (
          <Link
            key={href}
            href={href}
            aria-label={label}
            className={`flex h-10 w-10 items-center justify-center rounded-lg ${
              pathname.startsWith(href)
                ? "bg-white text-emerald-900"
                : "text-emerald-100 hover:bg-white/10"
            }`}
          >
            <Icon className="h-5 w-5" />
          </Link>
        ))}
        <div className="flex-1" />
        <ThemeToggle />
      </nav>

      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="flex items-center justify-between border-b px-6 py-3">
          <span className="text-sm text-gray-500">
            {currentUser.full_name} ({currentUser.role})
          </span>
          <button onClick={() => logout.mutate()} className="text-sm underline">
            Cerrar sesión
          </button>
        </header>
        <main className="flex-1 overflow-y-auto">{children}</main>
      </div>
    </div>
  );
}
```

`ChatIcon`/`BookIcon`/`MediaIcon`/`AdminIcon` son componentes SVG pequeños en
`frontend/components/icons.tsx` — mismos trazos ya usados en el mockup
(`docs/design/amza_workspace_mockup/template.html`), no hace falta rediseñarlos.

---

## 4. Tema claro/oscuro — persistente, sin parpadeo

Hoy `globals.css` solo respeta `prefers-color-scheme` del sistema operativo — no hay forma de que
el usuario elija explícitamente. Hace falta un tercer estado: *seguir al sistema* (default) vs.
*forzado a claro* vs. *forzado a oscuro* — mismo patrón de tres estados ya validado en el mockup,
aplicado ahora a Tailwind v4 (config CSS-first, sin `tailwind.config.*`):

`frontend/app/globals.css`:

```css
@import "tailwindcss";

:root {
  --background: #ffffff;
  --foreground: #171717;
}

@theme inline {
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --font-sans: var(--font-geist-sans);
  --font-mono: var(--font-geist-mono);
}

/* El sistema decide, solo si el usuario no forzó un tema explícito. */
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --background: #0a0a0a;
    --foreground: #ededed;
  }
}

/* El toggle manual siempre gana, en ambas direcciones. */
:root[data-theme="dark"] {
  --background: #0a0a0a;
  --foreground: #ededed;
}

body {
  background: var(--background);
  color: var(--foreground);
  font-family: Arial, Helvetica, sans-serif;
}
```

`frontend/app/layout.tsx` — un script inline **antes** de que React hidrate evita el parpadeo de
tema incorrecto al cargar (lee `localStorage` directamente, no espera al JavaScript de React):

```tsx
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              try {
                var t = localStorage.getItem('amza-theme');
                if (t === 'light' || t === 'dark') document.documentElement.setAttribute('data-theme', t);
              } catch (e) {}
            `,
          }}
        />
      </head>
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
```

`suppressHydrationWarning` en `<html>` es obligatorio aquí: el script cambia `data-theme` antes de
que React hidrate, así que el marcado del servidor y el del cliente difieren intencionalmente en
ese único atributo — sin esto, React lo reporta como un error de hidratación que no lo es.

`frontend/components/theme-toggle.tsx` (nuevo, sin hook propio — un solo consumidor no justifica
extraer un `use-theme.ts` todavía, ver `03_Engineering_Principles.md` sobre abstracciones
prematuras):

```tsx
"use client";

import { useEffect, useState } from "react";

import { MoonIcon, SunIcon } from "@/components/icons";

export function ThemeToggle() {
  const [theme, setTheme] = useState<"light" | "dark" | null>(null);

  useEffect(() => {
    const stored = localStorage.getItem("amza-theme");
    setTheme(stored === "light" || stored === "dark" ? stored : null);
  }, []);

  function toggle() {
    const isDark = theme ? theme === "dark" : window.matchMedia("(prefers-color-scheme: dark)").matches;
    const next = isDark ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("amza-theme", next);
    setTheme(next);
  }

  return (
    <button
      onClick={toggle}
      aria-label="Cambiar tema claro u oscuro"
      className="flex h-10 w-10 items-center justify-center rounded-lg text-emerald-100 hover:bg-white/10"
    >
      {theme === "dark" ? <SunIcon className="h-4 w-4" /> : <MoonIcon className="h-4 w-4" />}
    </button>
  );
}
```

No se agrega `next-themes`: el problema es pequeño (un atributo + `localStorage`), y el proyecto ya
prefiere resolverlo a mano en vez de sumar una dependencia — mismo criterio que evitó `authlib` en
spec 008.

---

## 5. Rutas placeholder

`frontend/app/(workspace)/knowledge-base/page.tsx` (y análogos para `media/`, `admin/`) — Server
Component, sin `"use client"`, sin data-fetching:

```tsx
export default function KnowledgeBasePage() {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-2 text-center text-gray-500">
      <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-900">
        Próxima spec
      </span>
      <h2 className="text-lg font-semibold text-foreground">Base de conocimiento</h2>
      <p className="max-w-sm text-sm">
        Subir listas de precios, fichas técnicas y catálogos para que la IA los use al responder.
        Todavía no implementado.
      </p>
    </div>
  );
}
```

Existen como rutas reales — no un `if` de JavaScript decidiendo qué mostrar — porque cada sección de
la plataforma ya es su propia ruta en este proyecto; mantiene esa convención en vez de introducir un
patrón de "secciones" paralelo solo para estas cuatro.

---

## 6. Assets

`amza-logo.png` (ya en la raíz del repo desde la discusión de diseño de este rediseño) se copia a
`frontend/public/amza-logo.png` — es lo único que cambia fuera de `frontend/app/` y
`frontend/components/`.

---

## 7. Tests

Política vigente desde spec 008: este spec incluye pruebas de lo que introduce, y actualiza las que
su cambio de comportamiento rompe.

- `frontend/tests/e2e/advisor-workspace.spec.ts` (existente) — **debe actualizarse**, no solo seguir
  pasando por casualidad: hoy busca el nombre del usuario y el botón "Cerrar sesión" dentro de la
  página de oportunidades; con este spec esos elementos viven en `WorkspaceShell`, fuera de
  `opportunities/page.tsx`. El texto y el rol exacto no cambian (mismo `currentUser.full_name`,
  mismo "Cerrar sesión") — solo su ubicación en el árbol; los selectores por texto/rol deberían
  seguir funcionando sin cambios, los que dependían de la estructura del `<main>` original sí
  necesitan ajuste.
- Nuevo test e2e: cambiar el tema con el toggle, recargar la página (`page.reload()`), confirmar que
  el tema elegido persiste — valida el script anti-parpadeo de la sección 4, no solo el estado en
  memoria del componente.
- Nuevo test e2e: navegar a `/knowledge-base` (o cualquier placeholder) y confirmar que muestra
  "Próxima spec" en vez de un error o una página en blanco.
- Nada que probar en backend — este spec no lo toca.

---

## Próximo paso

Spec 012 — rediseño del panel de chat (estilo WhatsApp Web: lista de conversaciones con orden y
filtros, hilo de mensajes, panel de información del cliente con etiquetas/notas/seguimiento,
composer con emojis y adjuntos), usando `docs/design/amza_workspace_mockup/` como referencia visual
ya validada. Ese spec vive **dentro** de `WorkspaceShell` (construido aquí) — no lo reemplaza ni lo
modifica.

No avanzar a spec 013 (gobernanza de administradores) hasta que 012 esté implementado y validado —
orden acordado: 011 → 012 → 013 (gobernanza de administradores) → 014 (etiqueta de canal en
contactos) → 015 (integración de WhatsApp vía Evolution API) → 016 (panel de administración) → 017
(base de conocimiento) → 018 (multimedia).
