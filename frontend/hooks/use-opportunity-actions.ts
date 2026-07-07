import { useMutation, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/services/api";
import type { Opportunity } from "@/types/api";

interface AssignToAdvisorArgs {
  organizationSlug: string;
  opportunityId: string;
  advisorId: string;
}

export function useAssignToAdvisor() {
  const queryClient = useQueryClient();

  return useMutation<Opportunity, Error, AssignToAdvisorArgs>({
    mutationFn: ({ organizationSlug, opportunityId, advisorId }) =>
      apiFetch<Opportunity>(
        `/api/organizations/${organizationSlug}/opportunities/${opportunityId}/assign-advisor`,
        { method: "POST", body: JSON.stringify({ advisor_id: advisorId }) },
      ),
    onSuccess: (_data, { organizationSlug }) => {
      // removeQueries en vez de invalidateQueries -- invalidate solo marca la caché como vieja;
      // como no hay ningún componente suscrito a esta query mientras estamos en la página de
      // detalle, el refetch de verdad no ocurre hasta que /opportunities se vuelve a montar, y
      // para entonces ya mostró el dato viejo un instante antes de refrescar (el parpadeo que
      // se veía como bug en validación manual, y que además era asimétrico entre "tomar" y
      // "devolver" según qué pestaña hubiera quedado en caché). remove() borra el dato por
      // completo: al montar de nuevo, no hay nada viejo que mostrar -- solo el loading normal,
      // nunca un valor incorrecto.
      queryClient.removeQueries({ queryKey: ["opportunities", organizationSlug] });
    },
  });
}

interface ReturnToAIArgs {
  organizationSlug: string;
  opportunityId: string;
}

export function useReturnToAI() {
  const queryClient = useQueryClient();

  return useMutation<Opportunity, Error, ReturnToAIArgs>({
    mutationFn: ({ organizationSlug, opportunityId }) =>
      apiFetch<Opportunity>(
        `/api/organizations/${organizationSlug}/opportunities/${opportunityId}/return-to-ai`,
        { method: "POST" },
      ),
    onSuccess: (_data, { organizationSlug }) => {
      // removeQueries, no invalidateQueries -- misma razón que en useAssignToAdvisor arriba.
      queryClient.removeQueries({ queryKey: ["opportunities", organizationSlug] });
    },
  });
}
