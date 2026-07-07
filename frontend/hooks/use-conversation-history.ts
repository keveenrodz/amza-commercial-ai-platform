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
  });
}
