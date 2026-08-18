export default function KnowledgeBasePage() {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-2 text-center text-gray-500">
      <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-900">
        Próxima spec
      </span>
      <h2 className="text-lg font-semibold text-foreground">Base de conocimiento</h2>
      <p className="max-w-sm text-sm">
        Subir listas de precios, fichas técnicas y catálogos para que la IA los use al responder.
        Todavía no implementado.
      </p>
    </div>
  );
}
