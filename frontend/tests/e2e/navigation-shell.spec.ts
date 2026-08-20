import { expect, test } from "@playwright/test";

// Cubre lo que agrega spec 011: el shell de navegación (barra lateral, tema, rutas placeholder)
// -- no repite la cobertura de tabs/acciones ya probada en advisor-workspace.spec.ts.

const CURRENT_USER = {
  id: "advisor-1",
  organization_id: "org-1",
  organization_slug: "amza-empaques",
  full_name: "Juan Perez",
  email: "juan@gmail.com",
  role: "advisor",
  status: "active",
  is_primary: false,
};

test.beforeEach(async ({ page }) => {
  await page.route("**/api/auth/me", (route) => route.fulfill({ json: CURRENT_USER }));
  await page.route("**/api/organizations/*/opportunities", (route) =>
    route.fulfill({ json: [] }),
  );
});

test("el tema elegido persiste tras recargar la página", async ({ page }) => {
  await page.goto("/opportunities");

  await page.getByRole("button", { name: "Cambiar tema claro u oscuro" }).click();
  const themeAfterToggle = await page.evaluate(() =>
    document.documentElement.getAttribute("data-theme"),
  );
  expect(themeAfterToggle).not.toBeNull();

  await page.reload();
  const themeAfterReload = await page.evaluate(() =>
    document.documentElement.getAttribute("data-theme"),
  );
  expect(themeAfterReload).toBe(themeAfterToggle);
});

test("las rutas placeholder muestran 'Próxima spec' en vez de un error", async ({ page }) => {
  await page.goto("/knowledge-base");
  await expect(page.getByText("Próxima spec")).toBeVisible();
  // getByRole("heading", ...), no getByText -- spec 013b agrega un tooltip flotante al rail
  // nav con el mismo texto ("Base de conocimiento"), y un getByText sin acotar encuentra los
  // dos (modo estricto de Playwright lo rechaza).
  await expect(page.getByRole("heading", { name: "Base de conocimiento" })).toBeVisible();

  await page.getByRole("link", { name: "Multimedia" }).click();
  await expect(page).toHaveURL(/\/media$/);
  await expect(page.getByText("Próxima spec")).toBeVisible();
});
