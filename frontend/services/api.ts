// Único punto de acceso HTTP del frontend. El frontend nunca construye URLs del backend --
// siempre fetch("/api/..."), nunca fetch(process.env.BACKEND_URL + ...) ni nada equivalente.
// BACKEND_URL es server-only, la lee next.config.ts para el proxy (rewrites); ningún componente
// cliente debería conocerla ni importarla.

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

export async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  if (!path.startsWith("/api/")) {
    throw new Error(`apiFetch: la ruta debe empezar con "/api/", recibido "${path}"`);
  }

  const response = await fetch(path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new ApiError(response.status, body.detail ?? "Request failed");
  }

  // Nunca asumir que un 200 trae body JSON -- encontrado en validación manual (logout devolvía
  // 200 sin body, .json() lanzaba, la mutación fallaba en silencio antes de llegar a onSuccess).
  const text = await response.text();
  return (text.length > 0 ? JSON.parse(text) : undefined) as T;
}
