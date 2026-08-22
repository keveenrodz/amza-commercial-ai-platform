import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/services/api";
import type { ChannelHealthStatus } from "@/types/api";

// A diferencia de useWhatsAppStatus (sin refetchInterval a propósito -- ver ese hook), esto sí
// sondea en segundo plano: es justamente para avisarle al usuario si un canal se cayó sin que
// tenga /admin abierto. No genera tráfico externo nuevo por pestaña -- lee el resultado ya
// cacheado por ChannelHealthMonitor en el backend (una sola revisión real cada 60s ahí, sin
// importar cuántas pestañas consulten esto).
export function useChannelHealth() {
  return useQuery<ChannelHealthStatus>({
    queryKey: ["channelHealth"],
    queryFn: () => apiFetch<ChannelHealthStatus>("/api/health/status"),
    refetchInterval: 60_000,
    refetchIntervalInBackground: true,
  });
}
