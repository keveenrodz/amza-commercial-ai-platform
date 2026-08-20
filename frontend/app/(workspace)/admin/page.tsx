"use client";

import { useState } from "react";

import { useCurrentUser } from "@/hooks/use-current-user";
import {
  useActivateInternalUser,
  useCreateInternalUser,
  useDeactivateInternalUser,
  useInternalUsers,
  useUpdateInternalUser,
} from "@/hooks/use-internal-users";
import type { InternalUserSummary } from "@/types/api";

const ROLE_LABELS: Record<InternalUserSummary["role"], string> = {
  advisor: "Asesor",
  administrator: "Administrador",
};

// Solo cortesía de UX -- quien de verdad impide la acción es el backend (spec 014, sección 4).
// Si este chequeo y el del servidor se desincronizaran, el botón fallaría en el servidor en vez
// de ser una segunda capa de seguridad real.
function disabledReason(
  target: InternalUserSummary,
  currentUser: { id: string; is_primary: boolean },
): string | null {
  if (target.id === currentUser.id) return "No puedes desactivarte a ti mismo";
  if (target.role === "administrator" && !currentUser.is_primary) {
    return "Solo el administrador principal puede desactivar a otro administrador";
  }
  return null;
}

function EditUserRow({
  user,
  canEditEmail,
  orgSlug,
  onDone,
}: {
  user: InternalUserSummary;
  canEditEmail: boolean;
  orgSlug: string;
  onDone: () => void;
}) {
  const updateUser = useUpdateInternalUser();
  const [fullName, setFullName] = useState(user.full_name);
  const [email, setEmail] = useState(user.email);
  const [role, setRole] = useState<"advisor" | "administrator">(user.role);

  function handleSave() {
    if (!fullName.trim() || !email.trim()) return;
    updateUser.mutate(
      { organizationSlug: orgSlug, userId: user.id, fullName: fullName.trim(), email, role },
      { onSuccess: onDone },
    );
  }

  return (
    <tr className="border-b border-line bg-surface-2 last:border-0">
      <td className="px-4 py-2.5">
        <input
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          className="w-full rounded-lg border border-line bg-paper px-2 py-1.5 text-sm text-ink"
        />
      </td>
      <td className="px-4 py-2.5">
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          disabled={!canEditEmail}
          title={canEditEmail ? undefined : "Solo el administrador principal puede editar el email"}
          className="w-full rounded-lg border border-line bg-paper px-2 py-1.5 text-sm text-ink disabled:cursor-not-allowed disabled:opacity-50"
        />
      </td>
      <td className="px-4 py-2.5">
        <select
          value={role}
          onChange={(e) => setRole(e.target.value as "advisor" | "administrator")}
          disabled={user.is_primary}
          title={user.is_primary ? "El administrador principal no puede perder ese rol" : undefined}
          className="w-full rounded-lg border border-line bg-paper px-2 py-1.5 text-sm text-ink disabled:cursor-not-allowed disabled:opacity-50"
        >
          <option value="advisor">Asesor</option>
          <option value="administrator">Administrador</option>
        </select>
      </td>
      <td className="px-4 py-2.5" colSpan={2}>
        <div className="flex items-center justify-end gap-2">
          {updateUser.isError && (
            <p className="text-xs text-overdue">{updateUser.error.message}</p>
          )}
          <button
            onClick={onDone}
            className="rounded-lg border border-line px-3 py-1.5 text-xs font-semibold text-ink-muted hover:bg-surface"
          >
            Cancelar
          </button>
          <button
            onClick={handleSave}
            disabled={updateUser.isPending || !fullName.trim() || !email.trim()}
            className="rounded-lg bg-accent px-3 py-1.5 text-xs font-bold text-white hover:bg-accent-deep disabled:opacity-50"
          >
            {updateUser.isPending ? "Guardando..." : "Guardar"}
          </button>
        </div>
      </td>
    </tr>
  );
}

export default function AdminPage() {
  const { data: currentUser } = useCurrentUser();
  const { data: users, isLoading } = useInternalUsers(currentUser?.organization_slug);
  const createUser = useCreateInternalUser();
  const deactivateUser = useDeactivateInternalUser();
  const activateUser = useActivateInternalUser();

  const [showCreateForm, setShowCreateForm] = useState(false);
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<"advisor" | "administrator">("advisor");
  const [editingUserId, setEditingUserId] = useState<string | null>(null);

  if (!currentUser) {
    return <p className="flex-1 p-8">Cargando...</p>;
  }

  if (currentUser.role !== "administrator") {
    return (
      <main className="flex flex-1 flex-col items-center justify-center gap-2 p-10 text-center text-ink-muted">
        <h2 className="font-heading text-lg font-bold text-ink">Acceso restringido</h2>
        <p className="max-w-sm text-sm">
          Solo un administrador puede ver esta página.
        </p>
      </main>
    );
  }

  const orgSlug = currentUser.organization_slug;

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!fullName.trim() || !email.trim()) return;
    createUser.mutate(
      { organizationSlug: orgSlug, fullName: fullName.trim(), email: email.trim(), role },
      {
        onSuccess: () => {
          setFullName("");
          setEmail("");
          setRole("advisor");
          setShowCreateForm(false);
        },
      },
    );
  }

  return (
    <main className="flex-1 overflow-y-auto p-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="font-heading text-xl font-extrabold text-ink">Administración</h1>
        {!showCreateForm && (
          <button
            onClick={() => setShowCreateForm(true)}
            className="rounded-lg bg-accent px-4 py-2 font-heading text-sm font-bold text-white hover:bg-accent-deep"
          >
            + Agregar usuario
          </button>
        )}
      </div>

      {showCreateForm && (
        <form
          onSubmit={handleSubmit}
          className="mb-8 flex flex-wrap items-end gap-3 rounded-xl border border-line bg-surface p-4 shadow-card"
        >
          <div className="flex flex-col gap-1">
            <label className="text-xs font-semibold text-ink-muted">Nombre</label>
            <input
              autoFocus
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="Nombre completo"
              className="w-48 rounded-lg border border-line bg-paper px-3 py-2 text-sm text-ink"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs font-semibold text-ink-muted">Email de Google</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="nombre@gmail.com"
              className="w-56 rounded-lg border border-line bg-paper px-3 py-2 text-sm text-ink"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs font-semibold text-ink-muted">Rol</label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value as "advisor" | "administrator")}
              className="rounded-lg border border-line bg-paper px-3 py-2 text-sm text-ink"
            >
              <option value="advisor">Asesor</option>
              <option value="administrator">Administrador</option>
            </select>
          </div>
          <button
            type="submit"
            disabled={createUser.isPending || !fullName.trim() || !email.trim()}
            className="rounded-lg bg-accent px-4 py-2 font-heading text-sm font-bold text-white hover:bg-accent-deep disabled:opacity-50"
          >
            {createUser.isPending ? "Agregando..." : "Agregar"}
          </button>
          <button
            type="button"
            onClick={() => setShowCreateForm(false)}
            className="rounded-lg border border-line px-4 py-2 text-sm font-semibold text-ink-muted hover:bg-surface-2"
          >
            Cancelar
          </button>
          {createUser.isError && (
            <p className="w-full text-sm text-overdue">{createUser.error.message}</p>
          )}
        </form>
      )}

      {isLoading ? (
        <p className="text-sm text-ink-muted">Cargando usuarios...</p>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-line bg-surface shadow-card">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-line text-xs font-semibold text-ink-faint">
                <th className="px-4 py-3">Nombre</th>
                <th className="px-4 py-3">Email</th>
                <th className="px-4 py-3">Rol</th>
                <th className="px-4 py-3">Estado</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {(users ?? []).map((user) =>
                editingUserId === user.id ? (
                  <EditUserRow
                    key={user.id}
                    user={user}
                    canEditEmail={currentUser.is_primary}
                    orgSlug={orgSlug}
                    onDone={() => setEditingUserId(null)}
                  />
                ) : (
                  <UserRow
                    key={user.id}
                    user={user}
                    currentUser={currentUser}
                    orgSlug={orgSlug}
                    onEdit={() => setEditingUserId(user.id)}
                    deactivateUser={deactivateUser}
                    activateUser={activateUser}
                  />
                ),
              )}
            </tbody>
          </table>
        </div>
      )}

      {(deactivateUser.isError || activateUser.isError) && (
        <p className="mt-3 text-sm text-overdue">
          {deactivateUser.error?.message ?? activateUser.error?.message}
        </p>
      )}
    </main>
  );
}

function UserRow({
  user,
  currentUser,
  orgSlug,
  onEdit,
  deactivateUser,
  activateUser,
}: {
  user: InternalUserSummary;
  currentUser: { id: string; is_primary: boolean };
  orgSlug: string;
  onEdit: () => void;
  deactivateUser: ReturnType<typeof useDeactivateInternalUser>;
  activateUser: ReturnType<typeof useActivateInternalUser>;
}) {
  const reason = disabledReason(user, currentUser);
  const isActive = user.status === "active";

  return (
    <tr className="border-b border-line last:border-0">
      <td className="px-4 py-3">
        <span className="flex items-center gap-1.5 font-medium text-ink">
          {user.full_name}
          {user.is_primary && (
            <span className="rounded-full bg-accent-soft px-2 py-0.5 text-[10px] font-bold text-accent-deep">
              Principal
            </span>
          )}
        </span>
      </td>
      <td className="px-4 py-3 text-ink-muted">{user.email}</td>
      <td className="px-4 py-3 text-ink-muted">{ROLE_LABELS[user.role]}</td>
      <td className="px-4 py-3">
        <span
          className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${
            isActive ? "bg-accent-soft text-accent-deep" : "bg-surface-2 text-ink-faint"
          }`}
        >
          {isActive ? "Activo" : "Inactivo"}
        </span>
      </td>
      <td className="px-4 py-3 text-right">
        <div className="flex items-center justify-end gap-2">
          <button
            onClick={onEdit}
            className="rounded-lg border border-line px-3 py-1.5 text-xs font-semibold text-ink-muted hover:bg-surface-2"
          >
            Editar
          </button>
          {isActive ? (
            <button
              onClick={() => deactivateUser.mutate({ organizationSlug: orgSlug, userId: user.id })}
              disabled={reason !== null || deactivateUser.isPending}
              title={reason ?? undefined}
              className="rounded-lg border border-line px-3 py-1.5 text-xs font-semibold text-ink-muted hover:bg-surface-2 disabled:cursor-not-allowed disabled:opacity-40"
            >
              Desactivar
            </button>
          ) : (
            <button
              onClick={() => activateUser.mutate({ organizationSlug: orgSlug, userId: user.id })}
              disabled={activateUser.isPending}
              className="rounded-lg border border-line px-3 py-1.5 text-xs font-semibold text-accent-deep hover:bg-surface-2"
            >
              Activar
            </button>
          )}
        </div>
      </td>
    </tr>
  );
}
