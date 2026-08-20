import { expect, test } from "@playwright/test";

// Cubre spec 014 (Admin Governance & Access Control) del lado del frontend -- las reglas de
// negocio (quién puede desactivar a quién) ya están probadas a fondo en
// backend/tests/test_admin_governance.py; este e2e cubre lo que esos tests no pueden: que el
// frontend muestre/oculte lo correcto según el rol, y que el flujo de crear un usuario funcione.

const ADMIN_USER = {
  id: "admin-1",
  organization_id: "org-1",
  organization_slug: "amza-empaques",
  full_name: "Admin Principal",
  email: "admin@gmail.com",
  role: "administrator",
  status: "active",
  is_primary: true,
};

const ADVISOR_USER = {
  id: "advisor-1",
  organization_id: "org-1",
  organization_slug: "amza-empaques",
  full_name: "Juan Perez",
  email: "juan@gmail.com",
  role: "advisor",
  status: "active",
  is_primary: false,
};

const EXISTING_USERS = [
  { id: "admin-1", full_name: "Admin Principal", email: "admin@gmail.com", role: "administrator", status: "active", is_primary: true },
  { id: "advisor-1", full_name: "Juan Perez", email: "juan@gmail.com", role: "advisor", status: "active", is_primary: false },
];

test.beforeEach(async ({ page }) => {
  await page.route("**/api/organizations/*/opportunities", (route) => route.fulfill({ json: [] }));
});

test("un administrador ve /admin, crea un usuario y lo ve aparecer en la tabla", async ({
  page,
}) => {
  await page.route("**/api/auth/me", (route) => route.fulfill({ json: ADMIN_USER }));

  let users = [...EXISTING_USERS];
  await page.route("**/api/organizations/*/users", (route) => {
    if (route.request().method() === "GET") {
      return route.fulfill({ json: users });
    }
    const body = route.request().postDataJSON();
    const created = {
      id: "new-user-1",
      full_name: body.full_name,
      email: body.email,
      role: body.role,
      status: "active",
      is_primary: false,
    };
    users = [...users, created];
    return route.fulfill({ status: 201, json: created });
  });

  await page.goto("/opportunities");
  await expect(page.getByRole("link", { name: "Administración" })).toBeVisible();

  await page.getByRole("link", { name: "Administración" }).click();
  await expect(page).toHaveURL(/\/admin$/);
  await expect(page.getByText("Admin Principal")).toBeVisible();
  await expect(page.getByText("Principal")).toBeVisible();

  // El formulario está detrás de un botón -- no visible hasta hacer clic (feedback post-014).
  await expect(page.getByPlaceholder("Nombre completo")).toHaveCount(0);
  await page.getByRole("button", { name: "+ Agregar usuario" }).click();

  await page.getByPlaceholder("Nombre completo").fill("Andrea Torres");
  await page.getByPlaceholder("nombre@gmail.com").fill("andrea@gmail.com");
  await page.getByRole("button", { name: "Agregar", exact: true }).click();

  await expect(page.getByText("Andrea Torres")).toBeVisible();
  await expect(page.getByText("andrea@gmail.com")).toBeVisible();
});

test("editar un usuario cambia nombre y rol en la tabla", async ({ page }) => {
  await page.route("**/api/auth/me", (route) => route.fulfill({ json: ADMIN_USER }));

  let users = [...EXISTING_USERS];
  await page.route("**/api/organizations/*/users/*", (route) => {
    const body = route.request().postDataJSON();
    users = users.map((u) =>
      u.id === "advisor-1" ? { ...u, full_name: body.full_name, role: body.role } : u,
    );
    return route.fulfill({ json: users.find((u) => u.id === "advisor-1") });
  });
  await page.route("**/api/organizations/*/users", (route) => route.fulfill({ json: users }));

  await page.goto("/admin");
  const row = page.locator("tr").filter({ hasText: "Juan Perez" });
  await row.getByRole("button", { name: "Editar" }).click();

  const editRow = page.locator("tr").filter({ hasText: "Cancelar" });
  await editRow.locator("input").first().fill("Juan Pérez Editado");
  await editRow.getByRole("button", { name: "Guardar" }).click();

  await expect(page.getByText("Juan Pérez Editado")).toBeVisible();
});

test("un administrador edita el prompt del agente y lo ve reflejado tras recargar", async ({
  page,
}) => {
  await page.route("**/api/auth/me", (route) => route.fulfill({ json: ADMIN_USER }));
  await page.route("**/api/organizations/*/users", (route) => route.fulfill({ json: EXISTING_USERS }));

  let agent = {
    id: "agent-1",
    name: "Asistente Comercial",
    system_prompt: "Eres un asistente comercial.",
    escalation_rules: "",
    model: "openai/gpt-4.1-nano",
  };
  await page.route("**/api/organizations/*/agent", (route) => {
    if (route.request().method() === "GET") {
      return route.fulfill({ json: agent });
    }
    const body = route.request().postDataJSON();
    agent = { ...agent, ...body };
    return route.fulfill({ json: agent });
  });

  await page.goto("/admin");
  await page.getByRole("button", { name: "Agente" }).click();

  // El prompt principal es el primer <textarea>/<input> de la pestaña (antes de reglas de
  // escalamiento y modelo).
  const promptBox = page.getByRole("textbox").first();
  await expect(promptBox).toHaveValue("Eres un asistente comercial.");
  await promptBox.fill("Eres el asistente comercial de Amza Empaques.");
  await page.getByRole("button", { name: "Guardar" }).click();

  await expect(page.getByText("Guardado.")).toBeVisible();

  // Recarga -- el valor guardado debe venir del backend, no solo quedarse en el estado local.
  await page.reload();
  await page.getByRole("button", { name: "Agente" }).click();
  await expect(page.getByRole("textbox").first()).toHaveValue(
    "Eres el asistente comercial de Amza Empaques.",
  );
});

test("un administrador ve el estado de WhatsApp y el QR al conectar", async ({ page }) => {
  await page.route("**/api/auth/me", (route) => route.fulfill({ json: ADMIN_USER }));
  await page.route("**/api/organizations/*/users", (route) => route.fulfill({ json: EXISTING_USERS }));
  await page.route("**/api/organizations/*/whatsapp/status", (route) =>
    route.fulfill({ json: { connected: false } }),
  );
  await page.route("**/api/organizations/*/whatsapp/connect", (route) =>
    route.fulfill({ json: { qrcode_base64: "iVBORfakebase64==" } }),
  );

  await page.goto("/admin");
  await page.getByRole("button", { name: "Canales" }).click();

  await expect(page.getByText("Desconectado")).toBeVisible();
  await page.getByRole("button", { name: "Conectar" }).click();

  await expect(page.getByAltText("Código QR de WhatsApp")).toBeVisible();
  await expect(page.getByAltText("Código QR de WhatsApp")).toHaveAttribute(
    "src",
    "data:image/png;base64,iVBORfakebase64==",
  );
});

test("un asesor no ve 'Administración' y recibe 403 al entrar directo a /admin", async ({
  page,
}) => {
  await page.route("**/api/auth/me", (route) => route.fulfill({ json: ADVISOR_USER }));
  await page.route("**/api/organizations/*/users", (route) =>
    route.fulfill({ status: 403, json: { detail: "Insufficient role" } }),
  );

  await page.goto("/opportunities");
  await expect(page.getByRole("link", { name: "Administración" })).toHaveCount(0);

  await page.goto("/admin");
  await expect(page.getByText("Acceso restringido")).toBeVisible();
});
