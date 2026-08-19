export default function LoginPage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6 bg-paper p-8">
      <h1 className="font-heading text-xl font-bold text-ink">Amza Commercial AI Platform</h1>
      <a
        href="/api/auth/google/login"
        className="rounded-full bg-accent px-6 py-3 font-heading font-bold text-white hover:bg-accent-deep"
      >
        Iniciar sesión con Google
      </a>
    </main>
  );
}
