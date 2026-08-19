"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { ChatBubble } from "@/components/chat-bubble";
import { ContactPanel } from "@/components/contact-panel";
import { DotsIcon, SearchIcon, StarIcon } from "@/components/icons";
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
  const [showSearch, setShowSearch] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [showContactPanel, setShowContactPanel] = useState(false);
  const [showReassignMenu, setShowReassignMenu] = useState(false);
  const [showChatMenu, setShowChatMenu] = useState(false);
  const reassignMenuRef = useRef<HTMLDivElement>(null);
  const chatMenuRef = useRef<HTMLDivElement>(null);

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

  if (!currentUser || isLoading || !history) {
    return <p className="p-8">Cargando...</p>;
  }

  const { opportunity, contact, follow_up: followUp, messages } = history;
  const isMine = opportunity.assigned_advisor_id === currentUser.id;
  const dayGroups = groupMessagesByDay(messages);
  const orgSlug = currentUser.organization_slug;

  return (
    <div className="flex h-full">
      <div className="mx-auto flex h-full w-full max-w-2xl flex-col p-8">
        <Link href="/opportunities" className="text-sm underline">
          ← Volver
        </Link>

        <div className="mt-4 mb-2 flex items-center gap-3">
          <button
            onClick={() => setShowContactPanel((v) => !v)}
            aria-label="Ver información del cliente"
            className="flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-full bg-emerald-100 text-sm font-semibold text-emerald-900 dark:bg-emerald-900 dark:text-emerald-100"
          >
            {initials(contact.display_name)}
          </button>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-1.5">
              <h1 className="truncate text-xl font-semibold">{contact.display_name}</h1>
              <button
                onClick={() =>
                  toggleFavorite.mutate({
                    organizationSlug: orgSlug,
                    opportunityId: opportunity.id,
                    contactId: opportunity.contact_id,
                  })
                }
                aria-label="Marcar como preferido"
                className={contact.is_favorite ? "text-amber-500" : "text-gray-400"}
              >
                <StarIcon filled={contact.is_favorite} className="h-4 w-4" />
              </button>
            </div>
            <div className="mt-1 flex flex-wrap items-center gap-1.5">
              <ChannelChip channelType={opportunity.channel_type} />
              <StatusChip opportunity={opportunity} currentUserId={currentUser.id} />
              {followUp && <FollowUpChip followUp={followUp} />}
            </div>
          </div>
          <button
            onClick={() => setShowSearch((v) => !v)}
            aria-label="Buscar en la conversación"
            className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800"
          >
            <SearchIcon className="h-4 w-4" />
          </button>
          {isMine && (
            <div className="relative" ref={chatMenuRef}>
              <button
                onClick={() => setShowChatMenu((v) => !v)}
                aria-label="Más opciones"
                className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800"
              >
                <DotsIcon className="h-4 w-4" />
              </button>
              {showChatMenu && (
                <div className="absolute right-0 z-30 mt-1 w-48 rounded-lg border bg-white py-1 shadow-lg dark:border-gray-700 dark:bg-gray-900">
                  <button
                    onClick={() => {
                      setUnread.mutate({
                        organizationSlug: orgSlug,
                        opportunityId: opportunity.id,
                        unread: !opportunity.has_unread_messages,
                      });
                      setShowChatMenu(false);
                    }}
                    className="w-full px-3 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-800"
                  >
                    {opportunity.has_unread_messages ? "Marcar como leída" : "Marcar como no leída"}
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        {showSearch && (
          <div className="mb-3 flex items-center gap-2 rounded-lg border px-3 py-2">
            <SearchIcon className="h-4 w-4 flex-shrink-0 text-gray-400" />
            <input
              autoFocus
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Buscar en esta conversación"
              className="w-full bg-transparent text-sm outline-none"
            />
          </div>
        )}

        <div className="flex-1 overflow-y-auto">
          <div className="flex flex-col gap-4">
            {dayGroups.map((group) => (
              <div key={group.label}>
                <div className="mb-2 flex justify-center">
                  <span className="rounded-full border px-3 py-0.5 text-xs text-gray-500">
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

        {isMine && (
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
        )}

        {sendMessage.isError && (
          <p className="mt-2 text-sm text-red-600">
            No se pudo enviar el mensaje: {sendMessage.error.message}
          </p>
        )}

        <div className="mt-4 flex items-center gap-2">
          {!isMine ? (
            <>
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
                className="rounded bg-foreground px-4 py-2 text-background disabled:opacity-50"
              >
                {assignToAdvisor.isPending ? "Tomando..." : "Tomar conversación"}
              </button>
              {assignToAdvisor.isError && (
                <p className="mt-2 text-sm text-red-600">
                  No se pudo tomar la conversación: {assignToAdvisor.error.message}
                </p>
              )}
            </>
          ) : (
            <>
              <div className="relative" ref={reassignMenuRef}>
                <button
                  onClick={() => setShowReassignMenu((v) => !v)}
                  className="rounded border px-4 py-2"
                >
                  Reasignar
                </button>
                {showReassignMenu && (
                  <div className="absolute bottom-full left-0 z-30 mb-1 w-48 rounded-lg border bg-white py-1 shadow-lg dark:border-gray-700 dark:bg-gray-900">
                    <p className="px-3 py-1 text-xs text-gray-400">Reasignar a</p>
                    {(advisors ?? [])
                      .filter((a) => a.id !== currentUser.id)
                      .map((a) => (
                        <button
                          key={a.id}
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
                          className="w-full px-3 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-800"
                        >
                          {a.full_name}
                        </button>
                      ))}
                  </div>
                )}
              </div>
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
                className="rounded border px-4 py-2 disabled:opacity-50"
              >
                {returnToAI.isPending ? "Devolviendo..." : "Devolver a IA"}
              </button>
              {returnToAI.isError && (
                <p className="mt-2 text-sm text-red-600">
                  No se pudo devolver la conversación: {returnToAI.error.message}
                </p>
              )}
            </>
          )}
        </div>
      </div>

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
