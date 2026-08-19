export default function AdminPage() {
  return (
    <div className="flex h-full flex-1 flex-col items-center justify-center gap-2 text-center text-ink-muted">
      <span className="rounded-full bg-accent-soft px-3 py-1 text-xs font-heading font-bold text-accent-deep">
        Próxima spec
      </span>
      <h2 className="font-heading text-lg font-bold text-ink">Administración</h2>
      <p className="max-w-sm text-sm">
        Usuarios autorizados, conexión de WhatsApp, y el prompt del agente. Todavía no
        implementado.
      </p>
    </div>
  );
}
