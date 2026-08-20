import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/services/api";
import type { Agent } from "@/types/api";

export function useAgent(organizationSlug: string | undefined) {
  return useQuery<Agent>({
    queryKey: ["agent", organizationSlug],
    queryFn: () => apiFetch<Agent>(`/api/organizations/${organizationSlug}/agent`),
    enabled: organizationSlug !== undefined,
  });
}

interface UpdateAgentArgs {
  organizationSlug: string;
  systemPrompt: string;
  escalationRules: string;
  model: string;
}

export function useUpdateAgent() {
  const queryClient = useQueryClient();
  return useMutation<Agent, Error, UpdateAgentArgs>({
    mutationFn: ({ organizationSlug, systemPrompt, escalationRules, model }) =>
      apiFetch<Agent>(`/api/organizations/${organizationSlug}/agent`, {
        method: "PUT",
        body: JSON.stringify({
          system_prompt: systemPrompt,
          escalation_rules: escalationRules,
          model,
        }),
      }),
    onSuccess: (_data, { organizationSlug }) => {
      queryClient.invalidateQueries({ queryKey: ["agent", organizationSlug] });
    },
  });
}
