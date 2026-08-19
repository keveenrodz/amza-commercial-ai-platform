import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/services/api";
import type { AdvisorSummary } from "@/types/api";

export function useAdvisors(organizationSlug: string | undefined) {
  return useQuery<AdvisorSummary[]>({
    queryKey: ["advisors", organizationSlug],
    queryFn: () => apiFetch<AdvisorSummary[]>(`/api/organizations/${organizationSlug}/advisors`),
    enabled: organizationSlug !== undefined,
  });
}
