"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { ChannelDisconnectToast } from "@/components/channel-disconnect-toast";
import { AdminIcon, BookIcon, ChatIcon, MediaIcon } from "@/components/icons";
import { initials } from "@/components/status-chips";
import { ThemeToggle } from "@/components/theme-toggle";
import { useLogout } from "@/hooks/use-logout";
import type { CurrentUser } from "@/types/api";

const ROLE_LABELS: Record<CurrentUser["role"], string> = {
  advisor: "Asesor",
  administrator: "Administrador",
};

const NAV_ITEMS = [
  { href: "/opportunities", label: "Conversaciones", Icon: ChatIcon, adminOnly: false },
  { href: "/knowledge-base", label: "Base de conocimiento", Icon: BookIcon, adminOnly: false },
  { href: "/media", label: "Multimedia", Icon: MediaIcon, adminOnly: false },
  { href: "/admin", label: "Administración", Icon: AdminIcon, adminOnly: true },
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
  const [showAccountMenu, setShowAccountMenu] = useState(false);
  const accountMenuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleOutsideClick(event: MouseEvent) {
      if (accountMenuRef.current && !accountMenuRef.current.contains(event.target as Node)) {
        setShowAccountMenu(false);
      }
    }
    // Fase de captura -- ver memoria de decisiones técnicas: mismo patrón ya usado en los
    // demás menús flotantes (filtros, reasignar, tres-puntos del chat).
    document.addEventListener("click", handleOutsideClick, true);
    return () => document.removeEventListener("click", handleOutsideClick, true);
  }, []);

  return (
    <div className="flex h-screen">
      <nav
        className="flex w-[72px] flex-shrink-0 flex-col items-center border-r border-line bg-accent-deep py-[18px]"
        aria-label="Navegación principal"
      >
        <div className="mb-[22px] flex h-10 w-10 items-center justify-center rounded-[11px] bg-surface p-1.5 shadow-card">
          <Image src="/amza-logo.png" alt="Amza" width={28} height={28} className="h-full w-full object-contain" />
        </div>

        <div className="flex flex-1 flex-col gap-1.5">
          {NAV_ITEMS.filter(
            (item) => !item.adminOnly || currentUser.role === "administrator",
          ).map(({ href, label, Icon }) => (
            <Link
              key={href}
              href={href}
              aria-label={label}
              className={`group relative flex h-11 w-11 items-center justify-center rounded-xl ${
                pathname.startsWith(href)
                  ? "bg-surface text-accent-deep"
                  : "text-[#d9e6d3] hover:bg-white/10 hover:text-white"
              }`}
            >
              <Icon className="h-5 w-5" />
              <span
                className="pointer-events-none absolute left-[56px] top-1/2 z-20 -translate-y-1/2 whitespace-nowrap rounded-lg bg-ink px-2.5 py-1 font-heading text-[11.5px] font-semibold text-paper opacity-0 group-hover:opacity-100"
              >
                {label}
              </span>
            </Link>
          ))}
        </div>

        <div className="flex flex-col items-center gap-2.5">
          <ThemeToggle />
          <div className="relative" ref={accountMenuRef}>
            <button
              onClick={() => setShowAccountMenu((v) => !v)}
              title={`${currentUser.full_name} — ${ROLE_LABELS[currentUser.role]}`}
              aria-label="Cuenta"
              className="flex h-8 w-8 items-center justify-center rounded-full border-2 border-white/50 bg-surface font-heading text-xs font-bold text-accent-deep"
            >
              {initials(currentUser.full_name)}
            </button>
            {showAccountMenu && (
              <div className="absolute bottom-0 left-full z-30 ml-2 w-48 rounded-xl border border-line bg-surface p-2 shadow-card">
                <p className="truncate px-2 pt-1 font-heading text-sm font-bold text-ink">
                  {currentUser.full_name}
                </p>
                <p className="px-2 pb-2 text-xs text-ink-muted">
                  {ROLE_LABELS[currentUser.role]}
                </p>
                <button
                  onClick={() => logout.mutate()}
                  className="w-full rounded-lg border-t border-line px-2 pt-2 text-left text-sm text-ink-muted hover:text-overdue"
                >
                  Cerrar sesión
                </button>
              </div>
            )}
          </div>
        </div>
      </nav>

      {/* No es <main> -- cada página ya dibuja su propio <main>; anidar dos rompería la
          semántica HTML (un solo <main> por documento) y haría que selectores por rol
          "link"/"main" en tests confundieran la navegación de la barra lateral con el
          contenido de la página. */}
      <div className="flex min-h-0 flex-1 overflow-hidden bg-paper">{children}</div>
      <ChannelDisconnectToast />
    </div>
  );
}
