import { ChatIcon } from "@/components/icons";

// La lista vive en layout.tsx (spec 013b) -- esta página es solo el estado vacío que se ve
// mientras no hay ninguna conversación abierta, igual que .placeholder-panel del mockup.
export default function OpportunitiesPage() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center gap-2.5 p-10 text-center text-ink-muted">
      <div className="flex h-[52px] w-[52px] items-center justify-center rounded-2xl bg-surface text-accent shadow-card">
        <ChatIcon className="h-6 w-6" />
      </div>
      <h2 className="mt-1 font-heading text-base text-ink">Selecciona una conversación</h2>
      <p className="max-w-[340px] text-[13px]">
        Elige un contacto de la lista para ver el historial completo y responder.
      </p>
    </main>
  );
}
