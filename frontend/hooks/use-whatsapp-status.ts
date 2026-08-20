import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/services/api";
import type { WhatsAppStatus } from "@/types/api";

// Sin refetchInterval a propósito -- spec 016/017: "evitar escanear o reconectar el código QR
// constantemente" se traduce aquí en que esta pantalla nunca vuelve a preguntar sola, solo
// cuando el administrador pide el estado explícitamente (refetch manual con un botón).
export function useWhatsAppStatus(organizationSlug: string | undefined) {
  return useQuery<WhatsAppStatus>({
    queryKey: ["whatsappStatus", organizationSlug],
    queryFn: () =>
      apiFetch<WhatsAppStatus>(`/api/organizations/${organizationSlug}/whatsapp/status`),
    enabled: organizationSlug !== undefined,
  });
}

export function useConnectWhatsApp() {
  return useMutation<{ qrcode_base64: string }, Error, { organizationSlug: string }>({
    mutationFn: ({ organizationSlug }) =>
      apiFetch<{ qrcode_base64: string }>(
        `/api/organizations/${organizationSlug}/whatsapp/connect`,
        { method: "POST" },
      ),
  });
}

export function useDisconnectWhatsApp() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, { organizationSlug: string }>({
    mutationFn: ({ organizationSlug }) =>
      apiFetch<void>(`/api/organizations/${organizationSlug}/whatsapp/disconnect`, {
        method: "POST",
      }),
    onSuccess: (_data, { organizationSlug }) => {
      queryClient.invalidateQueries({ queryKey: ["whatsappStatus", organizationSlug] });
    },
  });
}
