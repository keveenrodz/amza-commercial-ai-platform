import { useMutation, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/services/api";
import type { Message } from "@/types/api";

interface SendMessageArgs {
  organizationSlug: string;
  opportunityId: string;
  advisorId: string;
  content: string;
}

export function useSendMessage() {
  const queryClient = useQueryClient();

  return useMutation<Message, Error, SendMessageArgs>({
    mutationFn: ({ organizationSlug, opportunityId, advisorId, content }) =>
      apiFetch<Message>(
        `/api/organizations/${organizationSlug}/opportunities/${opportunityId}/messages`,
        { method: "POST", body: JSON.stringify({ advisor_id: advisorId, content }) },
      ),
    onSuccess: (_data, { organizationSlug, opportunityId }) => {
      // invalidateQueries alcanza aquí -- a diferencia de useAssignToAdvisor/useReturnToAI
      // (use-opportunity-actions.ts), esta página sigue montada con un observador activo sobre
      // conversationHistory cuando la mutación resuelve: el refetch ocurre de inmediato, sin la
      // ventana de dato viejo que sí existía para la lista de oportunidades.
      queryClient.invalidateQueries({
        queryKey: ["conversationHistory", organizationSlug, opportunityId],
      });
    },
  });
}
