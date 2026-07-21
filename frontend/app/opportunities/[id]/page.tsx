"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";

import { useConversationHistory } from "@/hooks/use-conversation-history";
import { useAssignToAdvisor, useReturnToAI } from "@/hooks/use-opportunity-actions";
import { useRequireAuth } from "@/hooks/use-require-auth";
import { useSendMessage } from "@/hooks/use-send-message";

export default function OpportunityDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const { data: currentUser } = useRequireAuth();
  const { data: history, isLoading } = useConversationHistory(
    currentUser?.organization_slug,
    params.id,
  );
  const assignToAdvisor = useAssignToAdvisor();
  const returnToAI = useReturnToAI();
  const sendMessage = useSendMessage();
  const [draft, setDraft] = useState("");

  if (!currentUser || isLoading || !history) {
    return <p className="p-8">Cargando...</p>;
  }

  const { opportunity, messages } = history;
  const isMine = opportunity.assigned_advisor_id === currentUser.id;

  return (
    <main className="p-8 max-w-2xl mx-auto">
      <Link href="/opportunities" className="text-sm underline">
        ← Volver
      </Link>
      <h1 className="text-xl font-semibold mt-4 mb-2">
        Oportunidad {opportunity.id.slice(0, 8)}
      </h1>
      <p className="text-sm text-gray-500 mb-6">
        Estado: {opportunity.status} · Modo: {opportunity.attention_mode}
      </p>

      <div className="flex flex-col gap-3 mb-6">
        {messages.map((m) => (
          <div
            key={m.id}
            className={m.sender_role === "user" ? "self-start" : "self-end text-right"}
          >
            <p className="text-xs text-gray-400">{m.sender_role}</p>
            <p className="rounded border p-2 inline-block">{m.content}</p>
          </div>
        ))}
      </div>

      {isMine && (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (!draft.trim()) return;
            sendMessage.mutate(
              {
                organizationSlug: currentUser.organization_slug,
                opportunityId: opportunity.id,
                advisorId: currentUser.id,
                content: draft,
              },
              { onSuccess: () => setDraft("") },
            );
          }}
          className="mb-6 flex gap-2"
        >
          <input
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="Escribe tu respuesta..."
            className="flex-1 rounded border px-3 py-2"
            disabled={sendMessage.isPending}
          />
          <button
            type="submit"
            disabled={sendMessage.isPending || !draft.trim()}
            className="rounded bg-foreground px-4 py-2 text-background disabled:opacity-50"
          >
            {sendMessage.isPending ? "Enviando..." : "Enviar"}
          </button>
        </form>
      )}

      {sendMessage.isError && (
        <p className="mb-4 text-sm text-red-600">
          No se pudo enviar el mensaje: {sendMessage.error.message}
        </p>
      )}

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
    </main>
  );
}
