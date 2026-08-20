import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/services/api";
import type { InternalUserSummary } from "@/types/api";

export function useInternalUsers(organizationSlug: string | undefined) {
  return useQuery<InternalUserSummary[]>({
    queryKey: ["internalUsers", organizationSlug],
    queryFn: () =>
      apiFetch<InternalUserSummary[]>(`/api/organizations/${organizationSlug}/users`),
    enabled: organizationSlug !== undefined,
  });
}

interface CreateInternalUserArgs {
  organizationSlug: string;
  fullName: string;
  email: string;
  role: "advisor" | "administrator";
}

export function useCreateInternalUser() {
  const queryClient = useQueryClient();
  return useMutation<InternalUserSummary, Error, CreateInternalUserArgs>({
    mutationFn: ({ organizationSlug, fullName, email, role }) =>
      apiFetch<InternalUserSummary>(`/api/organizations/${organizationSlug}/users`, {
        method: "POST",
        body: JSON.stringify({ full_name: fullName, email, role }),
      }),
    onSuccess: (_data, { organizationSlug }) => {
      queryClient.invalidateQueries({ queryKey: ["internalUsers", organizationSlug] });
    },
  });
}

interface UserActionArgs {
  organizationSlug: string;
  userId: string;
}

export function useDeactivateInternalUser() {
  const queryClient = useQueryClient();
  return useMutation<InternalUserSummary, Error, UserActionArgs>({
    mutationFn: ({ organizationSlug, userId }) =>
      apiFetch<InternalUserSummary>(
        `/api/organizations/${organizationSlug}/users/${userId}/deactivate`,
        { method: "POST" },
      ),
    onSuccess: (_data, { organizationSlug }) => {
      queryClient.invalidateQueries({ queryKey: ["internalUsers", organizationSlug] });
    },
  });
}

export function useActivateInternalUser() {
  const queryClient = useQueryClient();
  return useMutation<InternalUserSummary, Error, UserActionArgs>({
    mutationFn: ({ organizationSlug, userId }) =>
      apiFetch<InternalUserSummary>(
        `/api/organizations/${organizationSlug}/users/${userId}/activate`,
        { method: "POST" },
      ),
    onSuccess: (_data, { organizationSlug }) => {
      queryClient.invalidateQueries({ queryKey: ["internalUsers", organizationSlug] });
    },
  });
}
