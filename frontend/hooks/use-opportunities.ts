import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/services/api";
import type { OpenOpportunity } from "@/types/api";

export function useOpportunities(organizationSlug: string | undefined) {
  return useQuery<OpenOpportunity[]>({
    queryKey: ["opportunities", organizationSlug],
    queryFn: () =>
      apiFetch<OpenOpportunity[]>(`/api/organizations/${organizationSlug}/opportunities`),
    enabled: organizationSlug !== undefined,
  });
}
