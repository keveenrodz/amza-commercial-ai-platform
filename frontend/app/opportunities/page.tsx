"use client";

import Link from "next/link";
import { useState } from "react";

import { useLogout } from "@/hooks/use-logout";
import { useOpportunities } from "@/hooks/use-opportunities";
import { useRequireAuth } from "@/hooks/use-require-auth";

type Tab = "unassigned" | "mine" | "all";

export default function OpportunitiesPage() {
  const { data: currentUser, isLoading: userLoading } = useRequireAuth();
  const { data: opportunities, isLoading: oppsLoading } = useOpportunities(
    currentUser?.organization_slug,
  );
  const [tab, setTab] = useState<Tab>("unassigned");
  const logout = useLogout();

  if (userLoading || !currentUser) {
    return <p className="p-8">Cargando...</p>;
  }

  // Estado derivado, nunca guardado -- siempre un .filter() sobre el resultado de useQuery().
  const filtered = (opportunities ?? []).filter((o) => {
    if (tab === "unassigned") return o.assigned_advisor_id === null;
    if (tab === "mine") return o.assigned_advisor_id === currentUser.id;
    return true;
  });

  return (
    <main className="p-8">
      <header className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold">Oportunidades</h1>
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-500">
            {currentUser.full_name} ({currentUser.role})
          </span>
          <button onClick={() => logout.mutate()} className="text-sm underline">
            Cerrar sesión
          </button>
        </div>
      </header>

      <nav className="flex gap-4 mb-4">
        <button
          onClick={() => setTab("unassigned")}
          className={tab === "unassigned" ? "font-bold" : "text-gray-500"}
        >
          Sin asignar
        </button>
        <button
          onClick={() => setTab("mine")}
          className={tab === "mine" ? "font-bold" : "text-gray-500"}
        >
          Mías
        </button>
        <button
          onClick={() => setTab("all")}
          className={tab === "all" ? "font-bold" : "text-gray-500"}
        >
          Todas
        </button>
      </nav>

      {oppsLoading ? (
        <p>Cargando oportunidades...</p>
      ) : filtered.length === 0 ? (
        <p className="text-gray-500">No hay oportunidades en esta vista.</p>
      ) : (
        <ul className="flex flex-col gap-2">
          {filtered.map((o) => (
            <li key={o.id}>
              <Link
                href={`/opportunities/${o.id}`}
                className="block rounded border p-3 hover:bg-gray-50 dark:hover:bg-gray-900"
              >
                <div className="flex justify-between">
                  <span>{o.status}</span>
                  <span className="text-sm text-gray-500">{o.attention_mode}</span>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
