export default function KnowledgeBasePage() {
  return (
    <div className="flex h-full flex-1 flex-col items-center justify-center gap-2 text-center text-ink-muted">
      <span className="rounded-full bg-accent-soft px-3 py-1 text-xs font-heading font-bold text-accent-deep">
        Próxima spec
      </span>
      <h2 className="font-heading text-lg font-bold text-ink">Base de conocimiento</h2>
      <p className="max-w-sm text-sm">
        Subir listas de precios, fichas técnicas y catálogos para que la IA los use al responder.
        Todavía no implementado.
      </p>
    </div>
  );
}
