import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/services/api";
import type { CurrentUser } from "@/types/api";

export function useCurrentUser() {
  return useQuery<CurrentUser>({
    queryKey: ["currentUser"],
    queryFn: () => apiFetch<CurrentUser>("/api/auth/me"),
    retry: false,
  });
}
