import { useMutation, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/services/api";
import type { Opportunity } from "@/types/api";

interface SetUnreadArgs {
  organizationSlug: string;
  opportunityId: string;
  unread: boolean;
}

export function useSetUnread() {
  const queryClient = useQueryClient();
  return useMutation<Opportunity, Error, SetUnreadArgs>({
    mutationFn: ({ organizationSlug, opportunityId, unread }) =>
      apiFetch<Opportunity>(
        `/api/organizations/${organizationSlug}/opportunities/${opportunityId}/unread`,
        { method: "POST", body: JSON.stringify({ unread }) },
      ),
    onSuccess: (_data, { organizationSlug }) => {
      queryClient.invalidateQueries({ queryKey: ["opportunities", organizationSlug] });
    },
  });
}
