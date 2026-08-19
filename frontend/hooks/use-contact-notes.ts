import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/services/api";
import type { ContactNote } from "@/types/api";

export function useContactNotes(organizationSlug: string | undefined, contactId: string | undefined) {
  return useQuery<ContactNote[]>({
    queryKey: ["contactNotes", organizationSlug, contactId],
    queryFn: () =>
      apiFetch<ContactNote[]>(
        `/api/organizations/${organizationSlug}/contacts/${contactId}/notes`,
      ),
    enabled: organizationSlug !== undefined && contactId !== undefined,
  });
}

interface AddNoteArgs {
  organizationSlug: string;
  contactId: string;
  advisorId: string;
  content: string;
}

export function useAddContactNote() {
  const queryClient = useQueryClient();
  return useMutation<ContactNote, Error, AddNoteArgs>({
    mutationFn: ({ organizationSlug, contactId, advisorId, content }) =>
      apiFetch<ContactNote>(
        `/api/organizations/${organizationSlug}/contacts/${contactId}/notes`,
        { method: "POST", body: JSON.stringify({ advisor_id: advisorId, content }) },
      ),
    onSuccess: (_data, { organizationSlug, contactId }) => {
      queryClient.invalidateQueries({ queryKey: ["contactNotes", organizationSlug, contactId] });
    },
  });
}
