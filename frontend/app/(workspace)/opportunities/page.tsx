"use client";

import Link from "next/link";
import { useState } from "react";

import { SearchIcon } from "@/components/icons";
import { ChannelChip, StatusChip, initials } from "@/components/status-chips";
import { useCurrentUser } from "@/hooks/use-current-user";
import { useOpportunities } from "@/hooks/use-opportunities";

type Tab = "ai" | "mine" | "all";

export default function OpportunitiesPage() {
  const { data: currentUser } = useCurrentUser();
  const { data: opportunities, isLoading: oppsLoading } = useOpportunities(
    currentUser?.organization_slug,
  );
  const [tab, setTab] = useState<Tab>("ai");
  const [query, setQuery] = useState("");

  if (!currentUser) {
    return <p className="p-8">Cargando...</p>;
  }

  // Estado derivado, nunca guardado -- siempre un .filter() sobre el resultado de useQuery().
  const filtered = (opportunities ?? [])
    .filter((item) => {
      if (tab === "ai") return item.opportunity.attention_mode === "ai";
      if (tab === "mine") return item.opportunity.assigned_advisor_id === currentUser.id;
      return true;
    })
    .filter((item) =>
      query.trim() === ""
        ? true
        : item.contact.display_name.toLowerCase().includes(query.trim().toLowerCase()),
    );

  return (
    <main className="p-8">
      <h1 className="text-xl font-semibold mb-4">Oportunidades</h1>

      <div className="mb-4 flex items-center gap-2 rounded-lg border px-3 py-2">
        <SearchIcon className="h-4 w-4 text-gray-400" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Buscar contacto"
          className="w-full bg-transparent text-sm outline-none"
        />
      </div>

      <nav className="flex gap-4 mb-4">
        <button
          onClick={() => setTab("ai")}
          className={tab === "ai" ? "font-bold" : "text-gray-500"}
        >
          IA
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
          {filtered.map((item) => (
            <li key={item.opportunity.id}>
              <Link
                href={`/opportunities/${item.opportunity.id}`}
                className="flex items-center gap-3 rounded border p-3 hover:bg-gray-50 dark:hover:bg-gray-900"
              >
                <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-emerald-100 text-sm font-semibold text-emerald-900 dark:bg-emerald-900 dark:text-emerald-100">
                  {initials(item.contact.display_name)}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between gap-2">
                    <span className="truncate font-medium">{item.contact.display_name}</span>
                  </div>
                  <div className="mt-1 flex items-center gap-1.5">
                    <ChannelChip channelType={item.opportunity.channel_type} />
                    <StatusChip opportunity={item.opportunity} currentUserId={currentUser.id} />
                  </div>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
