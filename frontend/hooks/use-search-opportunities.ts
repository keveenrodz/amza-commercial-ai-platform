import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/services/api";
import type { OpenOpportunity } from "@/types/api";

// Reemplaza el filtro puramente client-side de spec 012 cuando el usuario escribe una consulta
// no vacía -- este endpoint también busca dentro del contenido de los mensajes, no solo el
// nombre del contacto.
export function useSearchOpportunities(
  organizationSlug: string | undefined,
  query: string,
) {
  const trimmed = query.trim();
  return useQuery<OpenOpportunity[]>({
    queryKey: ["opportunities", "search", organizationSlug, trimmed],
    queryFn: () =>
      apiFetch<OpenOpportunity[]>(
        `/api/organizations/${organizationSlug}/opportunities/search?q=${encodeURIComponent(trimmed)}`,
      ),
    enabled: organizationSlug !== undefined && trimmed !== "",
  });
}
