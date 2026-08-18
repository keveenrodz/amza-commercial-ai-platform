"use client";

import { useRequireAuth } from "@/hooks/use-require-auth";
import { WorkspaceShell } from "@/components/workspace-shell";

export default function WorkspaceLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { data: currentUser, isLoading } = useRequireAuth();

  if (isLoading || !currentUser) {
    return <p className="p-8">Cargando...</p>;
  }

  return <WorkspaceShell currentUser={currentUser}>{children}</WorkspaceShell>;
}
