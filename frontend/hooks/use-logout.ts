import { useMutation, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/services/api";

export function useLogout() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => apiFetch<void>("/api/auth/logout", { method: "POST" }),
    onSuccess: () => {
      queryClient.clear();
    },
  });
}
