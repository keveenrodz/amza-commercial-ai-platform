import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/services/api";
import type { ConversationHistory } from "@/types/api";

export function useConversationHistory(
  organizationSlug: string | undefined,
  opportunityId: string,
) {
  return useQuery<ConversationHistory>({
    queryKey: ["conversationHistory", organizationSlug, opportunityId],
    queryFn: () =>
      apiFetch<ConversationHistory>(
        `/api/organizations/${organizationSlug}/opportunities/${opportunityId}/history`,
      ),
    enabled: organizationSlug !== undefined,
    // Sin WebSocket/SSE todavía -- polling simple para que los mensajes nuevos (del cliente o de
    // la IA) aparezcan solos mientras se mira la conversación, sin tener que cambiar de chat o
    // recargar la página. React Query ya pausa esto solo cuando la pestaña no tiene foco
    // (refetchIntervalInBackground por defecto es false).
    refetchInterval: 4000,
  });
}
