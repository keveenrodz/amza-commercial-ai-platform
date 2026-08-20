"use client";

import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { ChatBubble } from "@/components/chat-bubble";
import { ContactPanel } from "@/components/contact-panel";
import {
  ChevronDownIcon,
  ChevronUpIcon,
  DotsIcon,
  LockIcon,
  SearchIcon,
  StarIcon,
} from "@/components/icons";
import { MessageComposer } from "@/components/message-composer";
import { ChannelChip, FollowUpChip, StatusChip, initials } from "@/components/status-chips";
import { useAdvisors } from "@/hooks/use-advisors";
import { useConversationHistory } from "@/hooks/use-conversation-history";
import { useCurrentUser } from "@/hooks/use-current-user";
import { useAssignToAdvisor, useReturnToAI } from "@/hooks/use-opportunity-actions";
import { useSendMessage } from "@/hooks/use-send-message";
import { useSetUnread } from "@/hooks/use-set-unread";
import { useToggleFavorite } from "@/hooks/use-toggle-favorite";
import { groupMessagesByDay } from "@/lib/date-groups";

export default function OpportunityDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const searchParams = useSearchParams();
  const { data: currentUser } = useCurrentUser();
  const { data: history, isLoading } = useConversationHistory(
    currentUser?.organization_slug,
    params.id,
  );
  const assignToAdvisor = useAssignToAdvisor();
  const returnToAI = useReturnToAI();
  const sendMessage = useSendMessage();
  const setUnread = useSetUnread();
  const toggleFavorite = useToggleFavorite();
  const { data: advisors } = useAdvisors(currentUser?.organization_slug);
  const [draft, setDraft] = useState("");
  // Precargado desde ?q= -- así un resultado de la búsqueda general (spec 013b/refinamientos)
  // abre la conversación con la búsqueda interna ya activa, resaltando y haciendo scroll al
  // mensaje que hizo match, en vez de solo mostrar la conversación desde el principio.
  const [showSearch, setShowSearch] = useState(() => Boolean(searchParams.get("q")));
  const [searchQuery, setSearchQuery] = useState(() => searchParams.get("q") ?? "");

  // Re-sincroniza desde ?q= cada vez que cambia la conversación -- /opportunities/[id] es la
  // misma instancia de componente para cualquier id (rutas hermanas bajo el mismo layout, spec
  // 013b), así que el useState de arriba solo corre una vez y se queda desactualizado si el
  // asesor va de un resultado de búsqueda a otro (o de un resultado a una conversación normal
  // desde la barra lateral, ya sin ?q=) sin desmontar esta página.
  useEffect(() => {
    const q = searchParams.get("q");
    setShowSearch(Boolean(q));
    setSearchQuery(q ?? "");
  }, [params.id, searchParams]);
  const [matchCount, setMatchCount] = useState(0);
  const [matchIndex, setMatchIndex] = useState(0);
  const [showContactPanel, setShowContactPanel] = useState(false);
  const [showReassignMenu, setShowReassignMenu] = useState(false);
  const [showChatMenu, setShowChatMenu] = useState(false);
  const reassignMenuRef = useRef<HTMLDivElement>(null);
  const chatMenuRef = useRef<HTMLDivElement>(null);
  const threadRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleOutsideClick(event: MouseEvent) {
      const target = event.target as Node;
      if (reassignMenuRef.current && !reassignMenuRef.current.contains(target)) {
        setShowReassignMenu(false);
      }
      if (chatMenuRef.current && !chatMenuRef.current.contains(target)) {
        setShowChatMenu(false);
      }
    }
    // Fase de captura -- ver memoria de decisiones técnicas: los ítems dentro de estos
    // menús cierran el propio menú de forma síncrona al hacer clic.
    document.addEventListener("click", handleOutsideClick, true);
    return () => document.removeEventListener("click", handleOutsideClick, true);
  }, []);

  const messages = history?.messages;
  const messageCountRef = useRef(0);

  // Con el polling de useConversationHistory (spec 013b), un mensaje nuevo del cliente o de la
  // IA ya llega solo -- pero sin esto la vista se quedaba en el mismo scrollTop de antes (el
  // navegador no sigue el fondo cuando el contenido crece). Solo baja el scroll si ya se estaba
  // cerca del final (o es la primera carga) -- si el asesor subió a leer historial, un mensaje
  // nuevo no debería arrastrarlo de vuelta abajo.
  useEffect(() => {
    const el = threadRef.current;
    if (!el || messages === undefined) return;
    const isFirstLoad = messageCountRef.current === 0;
    const grew = messages.length > messageCountRef.current;
    if (grew) {
      const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 150;
      if (isFirstLoad || nearBottom) el.scrollTop = el.scrollHeight;
    }
    messageCountRef.current = messages.length;
  }, [messages]);

  // Cuenta coincidencias cada vez que cambia la búsqueda o llegan mensajes nuevos (el historial
  // se refresca solo, spec 013b).
  useEffect(() => {
    if (!threadRef.current || !searchQuery.trim()) {
      setMatchCount(0);
      return;
    }
    setMatchCount(threadRef.current.querySelectorAll("mark").length);
  }, [searchQuery, messages?.length]);

  // Vuelve al primer match cada vez que cambia la búsqueda -- el efecto de abajo hace el scroll
  // real, este solo reinicia el índice.
  useEffect(() => {
    setMatchIndex(0);
  }, [searchQuery]);

  // Auto-scroll al match actual. Depende también de isLoading: al entrar desde un resultado de
  // búsqueda general, este efecto corre primero durante el render de "Cargando..." (threadRef
  // todavía null, no hace nada) y sin esta dependencia nunca se re-ejecutaba una vez el hilo real
  // se montaba con los <mark> ya en el DOM. isLoading es true->false una sola vez por conversación
  // (React Query, no por cada poll de refetchInterval con datos ya en caché), así que esto no
  // arrastra la vista de vuelta en cada mensaje nuevo mientras el usuario lee otra parte del hilo.
  useEffect(() => {
    if (!searchQuery.trim() || !threadRef.current) return;
    const marks = threadRef.current.querySelectorAll("mark");
    marks[matchIndex]?.scrollIntoView({ block: "center" });
  }, [searchQuery, matchIndex, isLoading]);

  if (!currentUser || isLoading || !history) {
    return <p className="flex-1 p-8">Cargando...</p>;
  }

  const { opportunity, contact, follow_up: followUp } = history;
  const isMine = opportunity.assigned_advisor_id === currentUser.id;
  const isAI = opportunity.attention_mode === "ai";
  const dayGroups = groupMessagesByDay(history.messages);
  const orgSlug = currentUser.organization_slug;
  const hasUnread = opportunity.unread_count > 0;

  const assignedAdvisorName = isMine
    ? currentUser.full_name
    : (advisors ?? []).find((a) => a.id === opportunity.assigned_advisor_id)?.full_name;

  function goToMatch(delta: number) {
    if (matchCount === 0) return;
    setMatchIndex((i) => (i + delta + matchCount) % matchCount);
  }

  return (
    <div className="flex min-w-0 flex-1">
      <main className="flex min-w-0 flex-1 flex-col bg-paper">
        <div className="flex items-center gap-3 border-b border-line bg-surface px-5 py-[13px]">
          <button
            onClick={() => setShowContactPanel((v) => !v)}
            aria-label="Ver información del cliente"
            className="flex h-[38px] w-[38px] flex-shrink-0 items-center justify-center rounded-full bg-surface-3 font-heading text-sm font-bold text-ink-muted"
          >
            {initials(contact.display_name)}
          </button>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-1.5">
              <h1 className="truncate font-heading text-[14.5px] font-extrabold text-ink">
                {contact.display_name}
              </h1>
              <button
                onClick={() =>
                  toggleFavorite.mutate({
                    organizationSlug: orgSlug,
                    opportunityId: opportunity.id,
                    contactId: opportunity.contact_id,
                  })
                }
                aria-label="Marcar como preferido"
                className={contact.is_favorite ? "text-gold" : "text-ink-faint"}
              >
                <StarIcon filled={contact.is_favorite} className="h-[15px] w-[15px]" />
              </button>
            </div>
            <div className="mt-[3px] flex flex-wrap items-center gap-1.5">
              <ChannelChip channelType={opportunity.channel_type} />
              {isAI ? (
                <StatusChip opportunity={opportunity} currentUserId={currentUser.id} />
              ) : (
                // Nombre real del asesor asignado (con puntico verde), no "Mía"/"Asignada" --
                // así se ve en el mockup: el chip siempre muestra a quién está asignada, sin
                // distinguir si ese "quién" es el usuario actual.
                <span className="inline-flex items-center gap-1 rounded-full bg-surface-2 px-1.5 py-0.5 font-heading text-[9.5px] font-bold tracking-wide text-ink">
                  <span className="h-1.5 w-1.5 flex-shrink-0 rounded-full bg-accent" />
                  {assignedAdvisorName ?? "Asesor"}
                </span>
              )}
              {followUp && <FollowUpChip followUp={followUp} />}
            </div>
          </div>

          <div className="flex flex-shrink-0 items-center gap-2">
            {isAI ? (
              <button
                onClick={() =>
                  assignToAdvisor.mutate(
                    {
                      organizationSlug: orgSlug,
                      opportunityId: opportunity.id,
                      advisorId: currentUser.id,
                    },
                    // Vuelve a la lista al terminar -- es la confirmación de que la acción
                    // funcionó (la oportunidad aparece en "Mías"), sin necesitar un popup aparte.
                    { onSuccess: () => router.push("/opportunities") },
                  )
                }
                disabled={assignToAdvisor.isPending}
                className="rounded-[9px] bg-accent px-3.5 py-2 font-heading text-[12.5px] font-bold text-white hover:bg-accent-deep disabled:opacity-50"
              >
                {assignToAdvisor.isPending ? "Tomando..." : "Tomar conversación"}
              </button>
            ) : (
              <>
                <div className="relative" ref={reassignMenuRef}>
                  <button
                    onClick={() => setShowReassignMenu((v) => !v)}
                    className="rounded-[9px] border border-line px-3.5 py-2 font-heading text-[12.5px] font-bold text-ink-muted hover:bg-surface-2"
                  >
                    Reasignar
                  </button>
                  {showReassignMenu && (
                    <div className="absolute right-0 z-30 mt-1.5 w-52 rounded-xl border border-line bg-surface py-1.5 shadow-card">
                      <p className="px-3 py-1 text-xs text-ink-muted">Reasignar a</p>
                      {(advisors ?? []).map((a) => {
                        const isCurrent = a.id === opportunity.assigned_advisor_id;
                        return (
                          <button
                            key={a.id}
                            disabled={isCurrent}
                            onClick={() => {
                              assignToAdvisor.mutate(
                                {
                                  organizationSlug: orgSlug,
                                  opportunityId: opportunity.id,
                                  advisorId: a.id,
                                },
                                { onSuccess: () => router.push("/opportunities") },
                              );
                              setShowReassignMenu(false);
                            }}
                            className="flex w-full items-center justify-between px-3 py-2 text-left text-sm text-ink hover:bg-surface-2 disabled:cursor-default disabled:text-ink-faint disabled:hover:bg-transparent"
                          >
                            {a.full_name}
                            {isCurrent && <span className="text-xs">· actual</span>}
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
                {isMine && (
                  <button
                    onClick={() =>
                      returnToAI.mutate(
                        {
                          organizationSlug: orgSlug,
                          opportunityId: opportunity.id,
                        },
                        { onSuccess: () => router.push("/opportunities") },
                      )
                    }
                    disabled={returnToAI.isPending}
                    className="rounded-[9px] border border-line px-3.5 py-2 font-heading text-[12.5px] font-bold text-ink-muted hover:bg-surface-2 disabled:opacity-50"
                  >
                    {returnToAI.isPending ? "Devolviendo..." : "Devolver a IA"}
                  </button>
                )}
              </>
            )}

            <button
              onClick={() => setShowSearch((v) => !v)}
              aria-label="Buscar en la conversación"
              className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full text-ink-muted hover:bg-surface-2"
            >
              <SearchIcon className="h-4 w-4" />
            </button>
            {isMine && (
              <div className="relative" ref={chatMenuRef}>
                <button
                  onClick={() => setShowChatMenu((v) => !v)}
                  aria-label="Más opciones"
                  className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full text-ink-muted hover:bg-surface-2"
                >
                  <DotsIcon className="h-4 w-4" />
                </button>
                {showChatMenu && (
                  <div className="absolute right-0 z-30 mt-1.5 w-48 rounded-xl border border-line bg-surface py-1 shadow-card">
                    <button
                      onClick={() => {
                        setUnread.mutate({
                          organizationSlug: orgSlug,
                          opportunityId: opportunity.id,
                          unread: !hasUnread,
                        });
                        setShowChatMenu(false);
                      }}
                      className="w-full px-3 py-2 text-left text-sm text-ink hover:bg-surface-2"
                    >
                      {hasUnread ? "Marcar como leída" : "Marcar como no leída"}
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {(assignToAdvisor.isError || returnToAI.isError) && (
          <p className="border-b border-line bg-surface px-5 py-2 text-sm text-overdue">
            {assignToAdvisor.isError &&
              `No se pudo tomar/reasignar la conversación: ${assignToAdvisor.error.message}`}
            {returnToAI.isError &&
              `No se pudo devolver la conversación: ${returnToAI.error.message}`}
          </p>
        )}

        {showSearch && (
          <div className="flex items-center gap-2 border-b border-line bg-surface px-5 py-2.5">
            <SearchIcon className="h-[15px] w-[15px] flex-shrink-0 text-ink-faint" />
            <input
              autoFocus
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Buscar en esta conversación"
              className="w-full bg-transparent text-[13px] outline-none placeholder:text-ink-faint"
            />
            {searchQuery.trim() && (
              <div className="flex flex-shrink-0 items-center gap-1">
                <span className="whitespace-nowrap text-[11.5px] text-ink-faint">
                  {matchCount === 0 ? "Sin coincidencias" : `${matchIndex + 1}/${matchCount}`}
                </span>
                {matchCount > 1 && (
                  <>
                    <button
                      onClick={() => goToMatch(-1)}
                      aria-label="Coincidencia anterior"
                      className="flex h-6 w-6 items-center justify-center rounded-md text-ink-muted hover:bg-surface-2"
                    >
                      <ChevronUpIcon className="h-3.5 w-3.5" />
                    </button>
                    <button
                      onClick={() => goToMatch(1)}
                      aria-label="Siguiente coincidencia"
                      className="flex h-6 w-6 items-center justify-center rounded-md text-ink-muted hover:bg-surface-2"
                    >
                      <ChevronDownIcon className="h-3.5 w-3.5" />
                    </button>
                  </>
                )}
              </div>
            )}
          </div>
        )}

        <div ref={threadRef} className="min-h-0 flex-1 overflow-y-auto px-6 py-5">
          <div className="flex flex-col gap-1">
            {dayGroups.map((group) => (
              <div key={group.label}>
                <div className="my-2.5 flex justify-center">
                  <span className="rounded-full border border-line bg-surface px-3 py-0.5 text-[11px] font-semibold text-ink-muted">
                    {group.label}
                  </span>
                </div>
                <div className="flex flex-col gap-2">
                  {group.messages.map((m) => (
                    <ChatBubble key={m.id} message={m} searchQuery={searchQuery} />
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="border-t border-line bg-surface px-5 py-3">
          {isMine ? (
            <MessageComposer
              value={draft}
              onChange={setDraft}
              onSubmit={() =>
                sendMessage.mutate(
                  {
                    organizationSlug: orgSlug,
                    opportunityId: opportunity.id,
                    advisorId: currentUser.id,
                    content: draft,
                  },
                  { onSuccess: () => setDraft("") },
                )
              }
              isSending={sendMessage.isPending}
              placeholder="Escribe tu respuesta..."
            />
          ) : (
            <div className="flex items-center gap-2 text-[12.5px] text-ink-muted">
              <LockIcon className="h-4 w-4 flex-shrink-0" />
              {isAI ? (
                <span>La IA está respondiendo. Toma la conversación para responder tú mismo.</span>
              ) : (
                <span>
                  Asignada a {assignedAdvisorName ?? "otro asesor"} — solo esa persona puede
                  responder.
                </span>
              )}
            </div>
          )}

          {sendMessage.isError && (
            <p className="mt-2 text-sm text-overdue">
              No se pudo enviar el mensaje: {sendMessage.error.message}
            </p>
          )}
        </div>
      </main>

      {showContactPanel && (
        <ContactPanel
          organizationSlug={orgSlug}
          opportunityId={opportunity.id}
          contactId={opportunity.contact_id}
          contact={contact}
          followUp={followUp}
          advisorId={currentUser.id}
          onClose={() => setShowContactPanel(false)}
        />
      )}
    </div>
  );
}
