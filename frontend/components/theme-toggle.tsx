"use client";

import { useEffect, useState } from "react";

import { MoonIcon, SunIcon } from "@/components/icons";

type Theme = "light" | "dark";

// Sin hook propio (use-theme.ts) -- un solo consumidor no justifica esa abstracción todavía
// (ver 03_Engineering_Principles.md sobre abstracciones prematuras).
export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme | null>(null);

  useEffect(() => {
    const stored = window.localStorage.getItem("amza-theme");
    setTheme(stored === "light" || stored === "dark" ? stored : null);
  }, []);

  function toggle() {
    const isDark = theme
      ? theme === "dark"
      : window.matchMedia("(prefers-color-scheme: dark)").matches;
    const next: Theme = isDark ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    window.localStorage.setItem("amza-theme", next);
    setTheme(next);
  }

  return (
    <button
      onClick={toggle}
      aria-label="Cambiar tema claro u oscuro"
      className="flex h-10 w-10 items-center justify-center rounded-lg text-emerald-100 hover:bg-white/10"
    >
      {theme === "dark" ? (
        <SunIcon className="h-4 w-4" />
      ) : (
        <MoonIcon className="h-4 w-4" />
      )}
    </button>
  );
}
