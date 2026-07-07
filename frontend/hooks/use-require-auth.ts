"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useCurrentUser } from "@/hooks/use-current-user";

// Sin middleware de Next.js en este spec (decisión de simplicidad, no limitación técnica -- ver
// spec 009 sección 5). El useEffect de abajo reacciona al resultado de useCurrentUser(), no hace
// ningún fetch propio -- react-query sigue siendo la única fuente de datos del cliente.
export function useRequireAuth() {
  const router = useRouter();
  const query = useCurrentUser();

  useEffect(() => {
    if (query.isError) {
      router.replace("/login");
    }
  }, [query.isError, router]);

  return query;
}
