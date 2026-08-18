"use client";

import Link from "next/link";
import { useState } from "react";

import { useCurrentUser } from "@/hooks/use-current-user";
import { useOpportunities } from "@/hooks/use-opportunities";

type Tab = "unassigned" | "mine" | "all";

export default function OpportunitiesPage() {
  const { data: currentUser } = useCurrentUser();
  const { data: opportunities, isLoading: oppsLoading } = useOpportunities(
    currentUser?.organization_slug,
  );
  const [tab, setTab] = useState<Tab>("unassigned");

  if (!currentUser) {
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
      <h1 className="text-xl font-semibold mb-6">Oportunidades</h1>

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
