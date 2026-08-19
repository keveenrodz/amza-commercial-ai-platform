"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";

import { ChatBubble } from "@/components/chat-bubble";
import { SearchIcon } from "@/components/icons";
import { MessageComposer } from "@/components/message-composer";
import { ChannelChip, StatusChip, initials } from "@/components/status-chips";
import { useConversationHistory } from "@/hooks/use-conversation-history";
import { useCurrentUser } from "@/hooks/use-current-user";
import { useAssignToAdvisor, useReturnToAI } from "@/hooks/use-opportunity-actions";
import { useSendMessage } from "@/hooks/use-send-message";
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
  const [draft, setDraft] = useState("");
  const [showSearch, setShowSearch] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  if (!currentUser || isLoading || !history) {
    return <p className="p-8">Cargando...</p>;
  }

  const { opportunity, contact, messages } = history;
  const isMine = opportunity.assigned_advisor_id === currentUser.id;
  const dayGroups = groupMessagesByDay(messages);

  return (
    <div className="mx-auto flex h-full max-w-2xl flex-col p-8">
      <Link href="/opportunities" className="text-sm underline">
        ← Volver
      </Link>

      <div className="mt-4 mb-2 flex items-center gap-3">
        <div className="flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-full bg-emerald-100 text-sm font-semibold text-emerald-900 dark:bg-emerald-900 dark:text-emerald-100">
          {initials(contact.display_name)}
        </div>
        <div className="min-w-0 flex-1">
          <h1 className="truncate text-xl font-semibold">{contact.display_name}</h1>
          <div className="mt-1 flex items-center gap-1.5">
            <ChannelChip channelType={opportunity.channel_type} />
            <StatusChip opportunity={opportunity} currentUserId={currentUser.id} />
          </div>
        </div>
        <button
          onClick={() => setShowSearch((v) => !v)}
          aria-label="Buscar en la conversación"
          className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800"
        >
          <SearchIcon className="h-4 w-4" />
        </button>
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
                organizationSlug: currentUser.organization_slug,
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

      <div className="mt-4">
        {!isMine ? (
          <>
            <button
              onClick={() =>
                assignToAdvisor.mutate(
                  {
                    organizationSlug: currentUser.organization_slug,
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
            <button
              onClick={() =>
                returnToAI.mutate(
                  {
                    organizationSlug: currentUser.organization_slug,
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
  );
}
