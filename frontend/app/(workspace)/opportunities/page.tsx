"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { FilterIcon, SearchIcon, SortIcon } from "@/components/icons";
import { ChannelChip, FollowUpChip, StatusChip, initials } from "@/components/status-chips";
import { useAdvisors } from "@/hooks/use-advisors";
import { useCurrentUser } from "@/hooks/use-current-user";
import { useOpportunities } from "@/hooks/use-opportunities";
import { useSearchOpportunities } from "@/hooks/use-search-opportunities";
import type { OpenOpportunity } from "@/types/api";

type Tab = "ai" | "mine" | "all";
type SortMode = "default" | "recent" | "unread" | "followup";

const SORT_MODES: SortMode[] = ["default", "recent", "unread", "followup"];
const SORT_LABELS: Record<SortMode, string> = {
  default: "",
  recent: "Recientes",
  unread: "No leídos",
  followup: "Seguimiento",
};

function allTags(items: OpenOpportunity[]): string[] {
  const set = new Set<string>();
  items.forEach((item) => item.contact.tags.forEach((t) => set.add(t)));
  return Array.from(set).sort();
}

export default function OpportunitiesPage() {
  const { data: currentUser } = useCurrentUser();
  const { data: opportunities, isLoading: oppsLoading } = useOpportunities(
    currentUser?.organization_slug,
  );
  const [tab, setTab] = useState<Tab>("ai");
  const [query, setQuery] = useState("");
  const trimmedQuery = query.trim();
  const { data: searchResults, isLoading: searchLoading } = useSearchOpportunities(
    currentUser?.organization_slug,
    query,
  );
  const { data: advisors } = useAdvisors(currentUser?.organization_slug);

  const [sortIndex, setSortIndex] = useState(0);
  const [assigneeFilter, setAssigneeFilter] = useState("all");
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [followupOnly, setFollowupOnly] = useState(false);
  const [tagFilters, setTagFilters] = useState<Set<string>>(new Set());
  const [showFiltersMenu, setShowFiltersMenu] = useState(false);
  const filtersMenuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleOutsideClick(event: MouseEvent) {
      if (filtersMenuRef.current && !filtersMenuRef.current.contains(event.target as Node)) {
        setShowFiltersMenu(false);
      }
    }
    // Fase de captura, no burbuja -- ver memoria de decisiones técnicas: un botón dentro
    // de este mismo menú puede cerrarlo de forma síncrona (ej. "Limpiar filtros"), y para
    // cuando el clic burbujea hasta document el nodo ya está desconectado del árbol.
    document.addEventListener("click", handleOutsideClick, true);
    return () => document.removeEventListener("click", handleOutsideClick, true);
  }, []);

  if (!currentUser) {
    return <p className="p-8">Cargando...</p>;
  }

  const usingSearch = trimmedQuery !== "";
  const isLoading = usingSearch ? searchLoading : oppsLoading;
  const baseItems = usingSearch ? (searchResults ?? []) : (opportunities ?? []);

  function matchesTab(item: OpenOpportunity): boolean {
    if (tab === "ai") return item.opportunity.attention_mode === "ai";
    if (tab === "mine") return item.opportunity.assigned_advisor_id === currentUser!.id;
    return true;
  }

  let items = baseItems.filter(matchesTab);
  if (tab === "all") {
    if (assigneeFilter === "ai") {
      items = items.filter((item) => item.opportunity.attention_mode === "ai");
    } else if (assigneeFilter !== "all") {
      items = items.filter((item) => item.opportunity.assigned_advisor_id === assigneeFilter);
    }
  }
  if (unreadOnly) items = items.filter((item) => item.opportunity.has_unread_messages);
  if (followupOnly) items = items.filter((item) => item.follow_up !== null);
  if (tagFilters.size > 0) {
    items = items.filter((item) => item.contact.tags.some((t) => tagFilters.has(t)));
  }

  items = items.slice();
  const sortMode = SORT_MODES[sortIndex];
  if (sortMode === "recent") {
    items.sort(
      (a, b) =>
        new Date(b.opportunity.last_activity_at).getTime() -
        new Date(a.opportunity.last_activity_at).getTime(),
    );
  } else if (sortMode === "unread") {
    items.sort(
      (a, b) => Number(b.opportunity.has_unread_messages) - Number(a.opportunity.has_unread_messages),
    );
  } else if (sortMode === "followup") {
    items.sort((a, b) => {
      if (!!a.follow_up === !!b.follow_up) {
        if (a.follow_up && b.follow_up) {
          const aOverdue = new Date(a.follow_up.due_at) < new Date();
          const bOverdue = new Date(b.follow_up.due_at) < new Date();
          return Number(bOverdue) - Number(aOverdue);
        }
        return 0;
      }
      return a.follow_up ? -1 : 1;
    });
  }

  const activeFilterCount =
    (tab === "all" && assigneeFilter !== "all" ? 1 : 0) +
    (unreadOnly ? 1 : 0) +
    (followupOnly ? 1 : 0) +
    (tagFilters.size > 0 ? 1 : 0);

  const tags = allTags(baseItems);

  function toggleTag(tag: string) {
    setTagFilters((prev) => {
      const next = new Set(prev);
      if (next.has(tag)) next.delete(tag);
      else next.add(tag);
      return next;
    });
  }

  function clearFilters() {
    setAssigneeFilter("all");
    setUnreadOnly(false);
    setFollowupOnly(false);
    setTagFilters(new Set());
  }

  return (
    <main className="p-8">
      <h1 className="text-xl font-semibold mb-4">Oportunidades</h1>

      <div className="mb-4 flex items-center gap-2 rounded-lg border px-3 py-2">
        <SearchIcon className="h-4 w-4 text-gray-400" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Buscar contacto o mensaje"
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

      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <button
            onClick={() => setSortIndex((i) => (i + 1) % SORT_MODES.length)}
            title={`Ordenar: ${sortMode === "default" ? "por defecto" : SORT_LABELS[sortMode].toLowerCase()}`}
            aria-label="Cambiar orden"
            className={`flex h-8 w-8 items-center justify-center rounded-full ${
              sortMode !== "default"
                ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200"
                : "text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800"
            }`}
          >
            <SortIcon className="h-4 w-4" />
          </button>
          {sortMode !== "default" && (
            <span className="text-xs font-semibold text-gray-500">{SORT_LABELS[sortMode]}</span>
          )}
        </div>

        <div className="relative">
          <button
            onClick={() => setShowFiltersMenu((v) => !v)}
            aria-label="Filtros"
            className={`relative flex h-8 w-8 items-center justify-center rounded-full ${
              activeFilterCount > 0
                ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200"
                : "text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800"
            }`}
          >
            <FilterIcon className="h-4 w-4" />
            {activeFilterCount > 0 && (
              <span className="absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-emerald-600 text-[10px] font-bold text-white">
                {activeFilterCount}
              </span>
            )}
          </button>

          {showFiltersMenu && (
            <div
              ref={filtersMenuRef}
              className="absolute right-0 z-30 mt-1 w-64 rounded-lg border bg-white p-1 shadow-lg dark:border-gray-700 dark:bg-gray-900"
            >
              {tab === "all" && (
                <>
                  <h5 className="px-2 pt-1.5 pb-1 text-[11px] font-semibold uppercase tracking-wide text-gray-400">
                    Asignado a
                  </h5>
                  {[["all", "Todos"], ["ai", "IA (sin asignar)"]]
                    .concat((advisors ?? []).map((a) => [a.id, a.full_name]))
                    .map(([value, label]) => (
                      <button
                        key={value}
                        onClick={() => setAssigneeFilter(value)}
                        className={`flex w-full items-center justify-between rounded px-2 py-1.5 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-800 ${
                          assigneeFilter === value ? "font-semibold text-emerald-700 dark:text-emerald-400" : ""
                        }`}
                      >
                        {label}
                        {assigneeFilter === value && <span>✓</span>}
                      </button>
                    ))}
                </>
              )}

              <h5 className="px-2 pt-1.5 pb-1 text-[11px] font-semibold uppercase tracking-wide text-gray-400">
                Estado
              </h5>
              <button
                onClick={() => setUnreadOnly((v) => !v)}
                className={`flex w-full items-center justify-between rounded px-2 py-1.5 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-800 ${
                  unreadOnly ? "font-semibold text-emerald-700 dark:text-emerald-400" : ""
                }`}
              >
                No leídos
                {unreadOnly && <span>✓</span>}
              </button>
              <button
                onClick={() => setFollowupOnly((v) => !v)}
                className={`flex w-full items-center justify-between rounded px-2 py-1.5 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-800 ${
                  followupOnly ? "font-semibold text-emerald-700 dark:text-emerald-400" : ""
                }`}
              >
                Seguimiento pendiente
                {followupOnly && <span>✓</span>}
              </button>

              <h5 className="px-2 pt-1.5 pb-1 text-[11px] font-semibold uppercase tracking-wide text-gray-400">
                Etiquetas
              </h5>
              {tags.length > 0 ? (
                <div className="flex flex-wrap gap-1.5 px-2 pb-1.5">
                  {tags.map((tag) => (
                    <button
                      key={tag}
                      onClick={() => toggleTag(tag)}
                      className={`rounded-full border px-2 py-1 text-[11px] font-medium ${
                        tagFilters.has(tag)
                          ? "border-emerald-600 bg-emerald-50 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200"
                          : "text-gray-600 dark:text-gray-300"
                      }`}
                    >
                      {tag}
                    </button>
                  ))}
                </div>
              ) : (
                <p className="px-2 pb-1.5 text-[11px] text-gray-400">Todavía no hay etiquetas creadas.</p>
              )}

              <button
                onClick={clearFilters}
                className="mt-1 w-full rounded px-2 py-1.5 text-left text-xs font-semibold text-gray-400 hover:text-red-600"
              >
                Limpiar filtros
              </button>
            </div>
          )}
        </div>
      </div>

      {isLoading ? (
        <p>Cargando oportunidades...</p>
      ) : items.length === 0 ? (
        <p className="text-gray-500">
          {usingSearch
            ? `Sin resultados para "${trimmedQuery}" en esta sección.`
            : "Ningún contacto coincide con estos filtros."}
        </p>
      ) : (
        <ul className="flex flex-col gap-2">
          {items.map((item) => (
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
                    <span className="flex min-w-0 items-center gap-1">
                      {item.contact.is_favorite && (
                        <span className="text-amber-500" aria-label="Preferido">
                          ★
                        </span>
                      )}
                      <span className="truncate font-medium">{item.contact.display_name}</span>
                    </span>
                    {item.opportunity.has_unread_messages && (
                      <span
                        aria-label="No leído"
                        className="h-2 w-2 flex-shrink-0 rounded-full bg-emerald-600"
                      />
                    )}
                  </div>
                  <div className="mt-1 flex flex-wrap items-center gap-1.5">
                    <ChannelChip channelType={item.opportunity.channel_type} />
                    <StatusChip opportunity={item.opportunity} currentUserId={currentUser.id} />
                    {item.follow_up && <FollowUpChip followUp={item.follow_up} />}
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
