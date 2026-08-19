import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/services/api";
import type { OpenOpportunity } from "@/types/api";

export function useOpportunities(organizationSlug: string | undefined) {
  return useQuery<OpenOpportunity[]>({
    queryKey: ["opportunities", organizationSlug],
    queryFn: () =>
      apiFetch<OpenOpportunity[]>(`/api/organizations/${organizationSlug}/opportunities`),
    enabled: organizationSlug !== undefined,
    // Mismo motivo que useConversationHistory -- sin esto, un mensaje nuevo en otra conversación
    // (badge de no leído, orden por "recientes") solo se refleja al recargar la página.
    refetchInterval: 5000,
  });
}
