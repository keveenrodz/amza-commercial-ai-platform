export default function LoginPage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6 p-8">
      <h1 className="text-xl font-semibold">Amza Commercial AI Platform</h1>
      <a
        href="/api/auth/google/login"
        className="rounded-full bg-foreground px-6 py-3 text-background font-medium hover:bg-[#383838] dark:hover:bg-[#ccc]"
      >
        Iniciar sesión con Google
      </a>
    </main>
  );
}
