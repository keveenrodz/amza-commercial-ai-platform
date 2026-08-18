export default function AdminPage() {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-2 text-center text-gray-500">
      <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-900">
        Próxima spec
      </span>
      <h2 className="text-lg font-semibold text-foreground">Administración</h2>
      <p className="max-w-sm text-sm">
        Usuarios autorizados, conexión de WhatsApp, y el prompt del agente. Todavía no
        implementado.
      </p>
    </div>
  );
}
