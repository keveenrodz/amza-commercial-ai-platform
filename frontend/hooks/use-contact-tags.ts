import { useMutation, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/services/api";
import type { ContactSummary } from "@/types/api";

interface TagArgs {
  organizationSlug: string;
  opportunityId: string;
  contactId: string;
  tag: string;
}

function invalidate(
  queryClient: ReturnType<typeof useQueryClient>,
  { organizationSlug, opportunityId }: Pick<TagArgs, "organizationSlug" | "opportunityId">,
) {
  queryClient.invalidateQueries({
    queryKey: ["conversationHistory", organizationSlug, opportunityId],
  });
  queryClient.invalidateQueries({ queryKey: ["opportunities", organizationSlug] });
}

export function useAddContactTag() {
  const queryClient = useQueryClient();
  return useMutation<ContactSummary, Error, TagArgs>({
    mutationFn: ({ organizationSlug, contactId, tag }) =>
      apiFetch<ContactSummary>(
        `/api/organizations/${organizationSlug}/contacts/${contactId}/tags`,
        { method: "POST", body: JSON.stringify({ tag }) },
      ),
    onSuccess: (_data, args) => invalidate(queryClient, args),
  });
}

export function useRemoveContactTag() {
  const queryClient = useQueryClient();
  return useMutation<ContactSummary, Error, TagArgs>({
    mutationFn: ({ organizationSlug, contactId, tag }) =>
      apiFetch<ContactSummary>(
        `/api/organizations/${organizationSlug}/contacts/${contactId}/tags/${encodeURIComponent(tag)}`,
        { method: "DELETE" },
      ),
    onSuccess: (_data, args) => invalidate(queryClient, args),
  });
}
