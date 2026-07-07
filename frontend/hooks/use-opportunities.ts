import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/services/api";
import type { Opportunity } from "@/types/api";

export function useOpportunities(organizationSlug: string | undefined) {
  return useQuery<Opportunity[]>({
    queryKey: ["opportunities", organizationSlug],
    queryFn: () =>
      apiFetch<Opportunity[]>(`/api/organizations/${organizationSlug}/opportunities`),
    enabled: organizationSlug !== undefined,
  });
}
