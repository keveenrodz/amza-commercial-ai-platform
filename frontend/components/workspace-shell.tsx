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
        {/* No es <main> -- cada página ya dibuja su propio <main>; anidar dos rompería la
            semántica HTML (un solo <main> por documento) y haría que selectores por rol
            "link"/"main" en tests confundieran la navegación de la barra lateral con el
            contenido de la página. */}
        <div className="flex-1 overflow-y-auto">{children}</div>
      </div>
    </div>
  );
}
