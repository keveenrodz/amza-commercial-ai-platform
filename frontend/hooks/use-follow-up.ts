import { useMutation, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/services/api";
import type { FollowUp } from "@/types/api";

interface ScheduleFollowUpArgs {
  organizationSlug: string;
  opportunityId: string;
  advisorId: string;
  dueAt: string;
  reason: string;
}

function invalidate(
  queryClient: ReturnType<typeof useQueryClient>,
  organizationSlug: string,
  opportunityId: string,
) {
  queryClient.invalidateQueries({
    queryKey: ["conversationHistory", organizationSlug, opportunityId],
  });
  queryClient.invalidateQueries({ queryKey: ["opportunities", organizationSlug] });
}

export function useScheduleFollowUp() {
  const queryClient = useQueryClient();
  return useMutation<FollowUp, Error, ScheduleFollowUpArgs>({
    mutationFn: ({ organizationSlug, opportunityId, advisorId, dueAt, reason }) =>
      apiFetch<FollowUp>(
        `/api/organizations/${organizationSlug}/opportunities/${opportunityId}/follow-up`,
        {
          method: "POST",
          body: JSON.stringify({ advisor_id: advisorId, due_at: dueAt, reason }),
        },
      ),
    onSuccess: (_data, { organizationSlug, opportunityId }) =>
      invalidate(queryClient, organizationSlug, opportunityId),
  });
}

interface ResolveFollowUpArgs {
  organizationSlug: string;
  opportunityId: string;
}

export function useResolveFollowUp() {
  const queryClient = useQueryClient();
  return useMutation<FollowUp, Error, ResolveFollowUpArgs>({
    mutationFn: ({ organizationSlug, opportunityId }) =>
      apiFetch<FollowUp>(
        `/api/organizations/${organizationSlug}/opportunities/${opportunityId}/follow-up/resolve`,
        { method: "POST" },
      ),
    onSuccess: (_data, { organizationSlug, opportunityId }) =>
      invalidate(queryClient, organizationSlug, opportunityId),
  });
}
