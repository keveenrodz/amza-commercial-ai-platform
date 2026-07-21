import { expect, test } from "@playwright/test";

// Intercepta /api/* a nivel de navegador -- nunca llega al proxy de Next.js ni al backend real.
// La lógica de autenticación (Google OAuth, JWT, InternalUser activo) ya está probada a fondo
// en backend/tests/test_security_and_identity.py; este e2e cubre lo que esos tests no pueden:
// que el frontend consuma el contrato correctamente (tabs, navegación, botones de acción).

const CURRENT_USER = {
  id: "advisor-1",
  organization_id: "org-1",
  organization_slug: "amza-empaques",
  full_name: "Juan Perez",
  email: "juan@gmail.com",
  role: "advisor",
  status: "active",
};

const UNASSIGNED_OPPORTUNITY = {
  id: "opp-unassigned",
  contact_id: "contact-1",
  agent_id: "agent-1",
  assigned_advisor_id: null,
  attention_mode: "ai",
  status: "new",
  channel_type: "telegram",
  started_at: "2026-01-01T00:00:00Z",
  last_activity_at: "2026-01-01T00:00:00Z",
  closed_at: null,
};

const MY_OPPORTUNITY = {
  ...UNASSIGNED_OPPORTUNITY,
  id: "opp-mine",
  assigned_advisor_id: CURRENT_USER.id,
  attention_mode: "human",
  status: "waiting_for_advisor",
};

test.beforeEach(async ({ page }) => {
  await page.route("**/api/auth/me", (route) =>
    route.fulfill({ json: CURRENT_USER }),
  );
  await page.route("**/api/organizations/*/opportunities", (route) =>
    route.fulfill({ json: [UNASSIGNED_OPPORTUNITY, MY_OPPORTUNITY] }),
  );
});

test("las tres pestañas filtran correctamente", async ({ page }) => {
  await page.goto("/opportunities");

  await expect(page.getByText("Juan Perez (advisor)")).toBeVisible();

  // Sin asignar es la pestaña por default.
  await expect(page.getByRole("link", { name: /new/i })).toHaveCount(1);

  await page.getByRole("button", { name: "Mías" }).click();
  await expect(page.getByRole("link", { name: /waiting_for_advisor/i })).toHaveCount(1);

  await page.getByRole("button", { name: "Todas" }).click();
  await expect(page.getByRole("link")).toHaveCount(2);
});

test("tomar una conversación sin asignar llama al endpoint correcto", async ({ page }) => {
  await page.route("**/api/organizations/*/opportunities/opp-unassigned/history", (route) =>
    route.fulfill({
      json: { opportunity: UNASSIGNED_OPPORTUNITY, messages: [] },
    }),
  );

  let assignRequestBody: unknown;
  await page.route(
    "**/api/organizations/*/opportunities/opp-unassigned/assign-advisor",
    (route) => {
      assignRequestBody = route.request().postDataJSON();
      route.fulfill({ json: { ...UNASSIGNED_OPPORTUNITY, assigned_advisor_id: CURRENT_USER.id } });
    },
  );

  await page.goto("/opportunities/opp-unassigned");
  await page.getByRole("button", { name: "Tomar conversación" }).click();

  await expect.poll(() => assignRequestBody).toEqual({ advisor_id: CURRENT_USER.id });

  // Encontrado en validación manual: sin esto, el usuario se quedaba en la página de detalle
  // sin ninguna señal de que la acción funcionó. La navegación de vuelta a la lista es la
  // confirmación -- no hace falta un popup aparte.
  await expect(page).toHaveURL(/\/opportunities$/);
});

test("enviar un mensaje en una conversación propia llama al endpoint correcto", async ({
  page,
}) => {
  const initialMessages = [
    {
      id: "msg-1",
      sender_role: "user",
      content: "Busco cajas de arroz",
      content_type: "text",
      sent_at: "2026-01-01T00:00:00Z",
    },
  ];

  await page.route("**/api/organizations/*/opportunities/opp-mine/history", (route) =>
    route.fulfill({
      json: { opportunity: MY_OPPORTUNITY, messages: initialMessages },
    }),
  );

  let sendRequestBody: unknown;
  await page.route("**/api/organizations/*/opportunities/opp-mine/messages", (route) => {
    sendRequestBody = route.request().postDataJSON();
    route.fulfill({
      json: {
        id: "msg-2",
        sender_role: "advisor",
        content: "Claro, ¿cuántas unidades necesitas?",
        content_type: "text",
        sent_at: "2026-01-01T00:01:00Z",
      },
    });
  });

  await page.goto("/opportunities/opp-mine");
  await page.getByPlaceholder("Escribe tu respuesta...").fill("Claro, ¿cuántas unidades necesitas?");
  await page.getByRole("button", { name: "Enviar" }).click();

  await expect.poll(() => sendRequestBody).toEqual({
    advisor_id: CURRENT_USER.id,
    content: "Claro, ¿cuántas unidades necesitas?",
  });

  // El input se limpia al terminar -- confirmación visual de que el envío funcionó.
  await expect(page.getByPlaceholder("Escribe tu respuesta...")).toHaveValue("");
});

test("sin sesión redirige a /login", async ({ page }) => {
  await page.unroute("**/api/auth/me");
  await page.route("**/api/auth/me", (route) =>
    route.fulfill({ status: 401, json: { detail: "Not authenticated" } }),
  );

  await page.goto("/opportunities");
  await expect(page).toHaveURL(/\/login$/);
  await expect(page.getByRole("link", { name: "Iniciar sesión con Google" })).toBeVisible();
});
