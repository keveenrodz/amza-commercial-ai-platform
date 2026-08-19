"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { FilterIcon, SearchIcon, SortIcon } from "@/components/icons";
import { ChannelChip, FollowUpChip, StatusChip, initials } from "@/components/status-chips";
import { useAdvisors } from "@/hooks/use-advisors";
import { useCurrentUser } from "@/hooks/use-current-user";
import { useOpportunities } from "@/hooks/use-opportunities";
import { useSearchOpportunities } from "@/hooks/use-search-opportunities";
import type { OpenOpportunity } from "@/types/api";

// La columna de lista vive en el layout (no en page.tsx) a propósito -- spec 013b: se comparte
// entre /opportunities y /opportunities/[id] (hermanos bajo este layout), así que sigue montada
// (con su estado de tabs/búsqueda/filtros intacto) al abrir o cerrar una conversación, igual que
// en el mockup (lista + chat + panel de cliente, todo visible a la vez).

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

export default function OpportunitiesLayout({ children }: { children: React.ReactNode }) {
  const params = useParams<{ id?: string }>();
  const selectedId = params.id;
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
    <div className="flex h-full w-full">
      <section
        aria-label="Lista de conversaciones"
        className="flex w-80 flex-shrink-0 flex-col border-r border-line bg-surface"
      >
        <div className="border-b border-line px-4 pt-[18px] pb-2.5">
          <h1 className="mb-0.5 font-heading text-[17px] font-extrabold tracking-tight text-ink">
            Conversaciones
          </h1>
          <p className="mb-3 text-xs text-ink-muted">Atención comercial</p>

          <div className="mb-3 flex items-center gap-2 rounded-[9px] bg-surface-2 px-2.5 py-2">
            <SearchIcon className="h-[15px] w-[15px] flex-shrink-0 text-ink-faint" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Buscar contacto o mensaje"
              className="w-full bg-transparent text-[13px] outline-none placeholder:text-ink-faint"
            />
          </div>

          <nav className="mb-2.5 flex gap-1.5">
            {(["ai", "mine", "all"] as const).map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`flex-1 whitespace-nowrap rounded-lg px-1.5 py-1.5 font-heading text-[11.5px] font-bold ${
                  tab === t ? "bg-accent text-white" : "bg-surface-2 text-ink-muted"
                }`}
              >
                {t === "ai" ? "IA" : t === "mine" ? "Mías" : "Todas"}
              </button>
            ))}
          </nav>

          <div className="relative flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <button
                onClick={() => setSortIndex((i) => (i + 1) % SORT_MODES.length)}
                title={`Ordenar: ${sortMode === "default" ? "por defecto" : SORT_LABELS[sortMode].toLowerCase()}`}
                aria-label="Cambiar orden"
                className={`inline-flex h-[30px] w-[30px] flex-shrink-0 items-center justify-center rounded-lg border ${
                  sortMode !== "default"
                    ? "border-accent bg-accent-soft text-accent-deep"
                    : "border-line bg-surface text-ink-muted hover:bg-surface-2"
                }`}
              >
                <SortIcon className="h-[15px] w-[15px]" />
              </button>
              {sortMode !== "default" && (
                <span className="text-[11px] font-semibold text-ink-muted">
                  {SORT_LABELS[sortMode]}
                </span>
              )}
            </div>

            <div className="relative">
              <button
                onClick={() => setShowFiltersMenu((v) => !v)}
                aria-label="Filtros"
                className={`relative inline-flex h-[30px] w-[30px] items-center justify-center rounded-lg border ${
                  activeFilterCount > 0
                    ? "border-accent bg-accent-soft text-accent-deep"
                    : "border-line bg-surface text-ink-muted hover:bg-surface-2"
                }`}
              >
                <FilterIcon className="h-[15px] w-[15px]" />
                {activeFilterCount > 0 && (
                  <span className="absolute -right-1 -top-1 flex h-[14px] min-w-[14px] items-center justify-center rounded-full bg-accent px-[3px] text-[9px] font-bold tabular-nums text-white">
                    {activeFilterCount}
                  </span>
                )}
              </button>

              {showFiltersMenu && (
                <div
                  ref={filtersMenuRef}
                  className="absolute right-0 z-30 mt-1.5 w-[230px] rounded-xl border border-line bg-surface p-2.5 shadow-card"
                >
                  {tab === "all" && (
                    <>
                      <h5 className="mx-1 mt-0.5 mb-1.5 font-heading text-[10.5px] uppercase tracking-wide text-ink-faint">
                        Asignado a
                      </h5>
                      {[["all", "Todos"], ["ai", "IA (sin asignar)"]]
                        .concat((advisors ?? []).map((a) => [a.id, a.full_name]))
                        .map(([value, label]) => (
                          <button
                            key={value}
                            onClick={() => setAssigneeFilter(value)}
                            className={`flex w-full items-center justify-between rounded-md px-1.5 py-1.5 text-left text-[12.5px] hover:bg-surface-2 ${
                              assigneeFilter === value ? "font-bold text-accent-deep" : ""
                            }`}
                          >
                            {label}
                            {assigneeFilter === value && <span>✓</span>}
                          </button>
                        ))}
                    </>
                  )}

                  <h5 className="mx-1 mt-2.5 mb-1.5 font-heading text-[10.5px] uppercase tracking-wide text-ink-faint">
                    Estado
                  </h5>
                  <button
                    onClick={() => setUnreadOnly((v) => !v)}
                    className={`flex w-full items-center justify-between rounded-md px-1.5 py-1.5 text-left text-[12.5px] hover:bg-surface-2 ${
                      unreadOnly ? "font-bold text-accent-deep" : ""
                    }`}
                  >
                    No leídos
                    {unreadOnly && <span>✓</span>}
                  </button>
                  <button
                    onClick={() => setFollowupOnly((v) => !v)}
                    className={`flex w-full items-center justify-between rounded-md px-1.5 py-1.5 text-left text-[12.5px] hover:bg-surface-2 ${
                      followupOnly ? "font-bold text-accent-deep" : ""
                    }`}
                  >
                    Seguimiento pendiente
                    {followupOnly && <span>✓</span>}
                  </button>

                  <h5 className="mx-1 mt-2.5 mb-1.5 font-heading text-[10.5px] uppercase tracking-wide text-ink-faint">
                    Etiquetas
                  </h5>
                  {tags.length > 0 ? (
                    <div className="flex flex-wrap gap-1.5 px-1 pb-1.5">
                      {tags.map((tag) => (
                        <button
                          key={tag}
                          onClick={() => toggleTag(tag)}
                          className={`rounded-full border px-2.5 py-1 text-[11px] font-semibold ${
                            tagFilters.has(tag)
                              ? "border-accent bg-accent-soft text-accent-deep"
                              : "border-line text-ink-muted"
                          }`}
                        >
                          {tag}
                        </button>
                      ))}
                    </div>
                  ) : (
                    <p className="px-1 pb-1.5 text-[11.5px] text-ink-faint">
                      Todavía no hay etiquetas creadas.
                    </p>
                  )}

                  <button
                    onClick={clearFilters}
                    className="mt-1.5 w-full border-t border-line px-1.5 py-1.5 text-left text-[11.5px] font-bold text-ink-muted hover:text-overdue"
                  >
                    Limpiar filtros
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto">
          {isLoading ? (
            <p className="p-5 text-center text-[12.5px] text-ink-faint">Cargando...</p>
          ) : items.length === 0 ? (
            <p className="p-5 text-center text-[12.5px] text-ink-faint">
              {usingSearch
                ? `Sin resultados para "${trimmedQuery}" en esta sección.`
                : "Ningún contacto coincide con estos filtros."}
            </p>
          ) : (
            items.map((item) => (
              <Link
                key={item.opportunity.id}
                href={`/opportunities/${item.opportunity.id}`}
                className={`grid grid-cols-[40px_1fr] gap-2.5 border-b border-line px-4 py-[11px] ${
                  item.opportunity.id === selectedId ? "bg-accent-soft" : "hover:bg-surface-2"
                }`}
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-surface-3 font-heading text-[13px] font-bold text-ink-muted">
                  {initials(item.contact.display_name)}
                </div>
                <div className="min-w-0">
                  <div className="flex items-baseline gap-1.5">
                    {item.contact.is_favorite && (
                      <span className="flex-shrink-0 text-gold" aria-label="Preferido">
                        ★
                      </span>
                    )}
                    <span className="truncate font-heading text-[13.5px] font-bold text-ink">
                      {item.contact.display_name}
                    </span>
                    {item.opportunity.has_unread_messages && (
                      <span
                        aria-label="No leído"
                        className="ml-auto h-2 w-2 flex-shrink-0 rounded-full bg-accent"
                      />
                    )}
                  </div>
                  <div className="mt-1.5 flex flex-wrap items-center gap-1">
                    <ChannelChip channelType={item.opportunity.channel_type} />
                    <StatusChip opportunity={item.opportunity} currentUserId={currentUser.id} />
                    {item.follow_up && <FollowUpChip followUp={item.follow_up} />}
                  </div>
                </div>
              </Link>
            ))
          )}
        </div>
      </section>

      {children}
    </div>
  );
}
