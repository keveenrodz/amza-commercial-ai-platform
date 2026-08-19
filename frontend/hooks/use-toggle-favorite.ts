import { useMutation, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/services/api";
import type { ContactSummary } from "@/types/api";

interface ToggleFavoriteArgs {
  organizationSlug: string;
  opportunityId: string;
  contactId: string;
}

export function useToggleFavorite() {
  const queryClient = useQueryClient();
  return useMutation<ContactSummary, Error, ToggleFavoriteArgs>({
    mutationFn: ({ organizationSlug, contactId }) =>
      apiFetch<ContactSummary>(
        `/api/organizations/${organizationSlug}/contacts/${contactId}/favorite`,
        { method: "POST" },
      ),
    onSuccess: (_data, { organizationSlug, opportunityId }) => {
      queryClient.invalidateQueries({
        queryKey: ["conversationHistory", organizationSlug, opportunityId],
      });
      queryClient.invalidateQueries({ queryKey: ["opportunities", organizationSlug] });
    },
  });
}
