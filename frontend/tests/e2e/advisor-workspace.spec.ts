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
  is_primary: false,
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
  unread_count: 0,
};

const MY_OPPORTUNITY = {
  ...UNASSIGNED_OPPORTUNITY,
  id: "opp-mine",
  contact_id: "contact-2",
  assigned_advisor_id: CURRENT_USER.id,
  attention_mode: "human",
  status: "waiting_for_advisor",
};

// spec 012 -- OpportunityResponse ya no viaja sola en el listado, cada fila trae su Contact
// (corrección de contrato: ninguna pantalla mostraba antes el nombre real del cliente).
// spec 013 -- ContactSummary gana tags/is_favorite, y cada item gana follow_up (sección 7).
const CONTACT_UNASSIGNED = {
  display_name: "Distribuidora El Roble",
  phone_number: null,
  tags: [],
  is_favorite: false,
};
const CONTACT_MINE = {
  display_name: "Litoempaques S.A.S.",
  phone_number: null,
  tags: [],
  is_favorite: false,
};

const OPEN_OPPORTUNITIES = [
  {
    opportunity: UNASSIGNED_OPPORTUNITY,
    contact: CONTACT_UNASSIGNED,
    follow_up: null,
    last_message_preview: null,
  },
  {
    opportunity: MY_OPPORTUNITY,
    contact: CONTACT_MINE,
    follow_up: null,
    last_message_preview: null,
  },
];

test.beforeEach(async ({ page }) => {
  await page.route("**/api/auth/me", (route) =>
    route.fulfill({ json: CURRENT_USER }),
  );
  await page.route("**/api/organizations/*/opportunities", (route) =>
    route.fulfill({ json: OPEN_OPPORTUNITIES }),
  );
});

test("las tres pestañas filtran correctamente", async ({ page }) => {
  await page.goto("/opportunities");

  // spec 013b -- el nombre/rol ya no vive en una barra visible siempre; está detrás del
  // avatar del rail (mismo patrón que el mockup), en un menú que se abre al hacer clic.
  await page.getByRole("button", { name: "Cuenta" }).click();
  await expect(page.getByText("Juan Perez")).toBeVisible();
  await expect(page.getByText("Asesor")).toBeVisible();
  await page.getByRole("heading", { name: "Conversaciones" }).click();

  const list = page.getByRole("region", { name: "Lista de conversaciones" });

  // IA es la pestaña por default (antes "Sin asignar" -- spec 012 la renombró).
  await expect(list.getByRole("link", { name: /Distribuidora El Roble/ })).toHaveCount(1);

  await page.getByRole("button", { name: "Mías" }).click();
  await expect(list.getByRole("link", { name: /Litoempaques/ })).toHaveCount(1);

  await page.getByRole("button", { name: "Todas" }).click();
  // Acotado a la región de la lista -- spec 013b la mueve al layout compartido, ya no vive
  // dentro de <main> (que ahora es solo el estado vacío o el detalle de una conversación).
  await expect(list.getByRole("link")).toHaveCount(2);
});

test("buscar por nombre de contacto llama al endpoint de búsqueda", async ({ page }) => {
  // spec 013 -- ya no es un filtro puramente client-side (spec 012); una consulta no vacía
  // dispara GET .../opportunities/search en vez de filtrar el listado en memoria.
  let searchUrl: string | undefined;
  await page.route("**/api/organizations/*/opportunities/search**", (route) => {
    searchUrl = route.request().url();
    route.fulfill({
      json: [
        {
          opportunity: MY_OPPORTUNITY,
          contact: CONTACT_MINE,
          follow_up: null,
          last_message_preview: null,
        },
      ],
    });
  });

  await page.goto("/opportunities");
  const list = page.getByRole("region", { name: "Lista de conversaciones" });
  await page.getByRole("button", { name: "Todas" }).click();
  await expect(list.getByRole("link")).toHaveCount(2);

  await page.getByPlaceholder("Buscar contacto o mensaje").fill("Lito");
  await expect(list.getByRole("link")).toHaveCount(1);
  await expect(page.getByText("Litoempaques S.A.S.")).toBeVisible();
  await expect.poll(() => searchUrl).toContain("q=Lito");
});

test("buscar por una palabra que solo existe en un mensaje encuentra la conversación", async ({
  page,
}) => {
  const MESSAGE_MATCH_CONTACT = { display_name: "Fábrica ABC", phone_number: null, tags: [], is_favorite: false };
  // attention_mode "human" a propósito -- la pestaña activa por defecto al entrar es "IA", y la
  // búsqueda es global (no debe filtrarse por la pestaña activa). Regresión real: el resultado
  // desaparecía en la pestaña "IA" porque el filtro de tab seguía aplicándose sobre los
  // resultados de búsqueda.
  const MESSAGE_MATCH_OPPORTUNITY = {
    ...UNASSIGNED_OPPORTUNITY,
    id: "opp-message-match",
    contact_id: "contact-3",
    attention_mode: "human",
  };

  // Este item NO existe en el listado base (OPEN_OPPORTUNITIES) -- solo lo devuelve el
  // endpoint de búsqueda, probando que el frontend de verdad llama a ese endpoint (que sí
  // busca dentro del contenido de los mensajes) en vez de filtrar el listado ya cargado.
  await page.route("**/api/organizations/*/opportunities/search**", (route) =>
    route.fulfill({
      json: [
        {
          opportunity: MESSAGE_MATCH_OPPORTUNITY,
          contact: MESSAGE_MATCH_CONTACT,
          follow_up: null,
          last_message_preview: null,
        },
      ],
    }),
  );

  await page.goto("/opportunities");
  await page.getByPlaceholder("Buscar contacto o mensaje").fill("guacal");
  await expect(page.getByText("Fábrica ABC")).toBeVisible();
});

test("tomar una conversación sin asignar llama al endpoint correcto", async ({ page }) => {
  await page.route("**/api/organizations/*/opportunities/opp-unassigned/history", (route) =>
    route.fulfill({
      json: {
        opportunity: UNASSIGNED_OPPORTUNITY,
        contact: CONTACT_UNASSIGNED,
        follow_up: null,
        messages: [],
      },
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
  await expect(page.getByRole("heading", { name: "Distribuidora El Roble" })).toBeVisible();
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
      json: {
        opportunity: MY_OPPORTUNITY,
        contact: CONTACT_MINE,
        follow_up: null,
        messages: initialMessages,
      },
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

test("buscar dentro de la conversación resalta la coincidencia", async ({ page }) => {
  const initialMessages = [
    {
      id: "msg-1",
      sender_role: "user",
      content: "Necesito cajas corrugadas para exportación",
      content_type: "text",
      sent_at: "2026-01-01T00:00:00Z",
    },
    {
      id: "msg-2",
      sender_role: "assistant",
      content: "¡Con gusto! ¿Cuántas unidades necesitas?",
      content_type: "text",
      sent_at: "2026-01-01T00:01:00Z",
    },
  ];

  await page.route("**/api/organizations/*/opportunities/opp-mine/history", (route) =>
    route.fulfill({
      json: {
        opportunity: MY_OPPORTUNITY,
        contact: CONTACT_MINE,
        follow_up: null,
        messages: initialMessages,
      },
    }),
  );

  await page.goto("/opportunities/opp-mine");
  await page.getByRole("button", { name: "Buscar en la conversación" }).click();
  await page.getByPlaceholder("Buscar en esta conversación").fill("corrugadas");

  await expect(page.locator("mark", { hasText: "corrugadas" })).toBeVisible();
});

test("panel de cliente: agregar una etiqueta y una nota", async ({ page }) => {
  let contactTags: string[] = [];
  const notes: { id: string; author_name: string; content: string; created_at: string }[] = [];

  await page.route("**/api/organizations/*/opportunities/opp-mine/history", (route) =>
    route.fulfill({
      json: {
        opportunity: MY_OPPORTUNITY,
        contact: { ...CONTACT_MINE, tags: contactTags },
        follow_up: null,
        messages: [],
      },
    }),
  );
  await page.route("**/api/organizations/*/contacts/*/tags", (route) => {
    const { tag } = route.request().postDataJSON();
    if (!contactTags.includes(tag)) contactTags = [...contactTags, tag];
    route.fulfill({ json: { ...CONTACT_MINE, tags: contactTags } });
  });
  await page.route("**/api/organizations/*/contacts/*/notes", (route) => {
    if (route.request().method() === "GET") {
      return route.fulfill({ json: notes });
    }
    const { content } = route.request().postDataJSON();
    const note = {
      id: `note-${notes.length + 1}`,
      author_name: CURRENT_USER.full_name,
      content,
      created_at: "2026-01-01T00:00:00Z",
    };
    notes.push(note);
    return route.fulfill({ json: note });
  });

  await page.goto("/opportunities/opp-mine");
  await page.getByRole("button", { name: "Ver información del cliente" }).click();

  await page.getByRole("button", { name: "+ Etiqueta" }).click();
  await page.getByPlaceholder("Nueva etiqueta").fill("Cliente frecuente");
  await page.getByPlaceholder("Nueva etiqueta").press("Enter");
  await expect(page.getByText("Cliente frecuente")).toBeVisible();

  await page
    .getByPlaceholder("Agregar una nota sobre este cliente...")
    .fill("Prefiere que lo contactemos por la tarde.");
  await page.getByRole("button", { name: "Guardar nota" }).click();
  await expect(page.getByText("Prefiere que lo contactemos por la tarde.")).toBeVisible();
});

test("programar un seguimiento y marcarlo resuelto", async ({ page }) => {
  let followUp: { id: string; due_at: string; reason: string } | null = null;

  await page.route("**/api/organizations/*/opportunities/opp-mine/history", (route) =>
    route.fulfill({
      json: { opportunity: MY_OPPORTUNITY, contact: CONTACT_MINE, follow_up: followUp, messages: [] },
    }),
  );
  await page.route("**/api/organizations/*/contacts/*/notes", (route) =>
    route.fulfill({ json: [] }),
  );
  await page.route("**/api/organizations/*/opportunities/opp-mine/follow-up", (route) => {
    const { reason } = route.request().postDataJSON();
    followUp = { id: "fu-1", due_at: "2099-01-15T14:00:00Z", reason };
    route.fulfill({ json: followUp });
  });
  await page.route(
    "**/api/organizations/*/opportunities/opp-mine/follow-up/resolve",
    (route) => {
      followUp = null;
      route.fulfill({ json: { id: "fu-1", due_at: "2099-01-15T14:00:00Z", reason: "" } });
    },
  );

  await page.goto("/opportunities/opp-mine");
  await page.getByRole("button", { name: "Ver información del cliente" }).click();

  await page.getByRole("button", { name: "+ Programar seguimiento" }).click();
  await page.getByText("Elige fecha y hora").click();
  // Nos movemos al mes siguiente para elegir un día garantizado en el futuro, sin depender
  // de qué día es "hoy" quando corre la prueba.
  await page.getByRole("button", { name: "Mes siguiente" }).click();
  await page.getByRole("button", { name: "15", exact: true }).click();
  await page.getByRole("button", { name: "Listo" }).click();

  await page.getByPlaceholder("Motivo del seguimiento").fill("Llamar para confirmar pedido");
  await page.getByRole("button", { name: "Guardar seguimiento" }).click();

  await expect(page.getByText("Llamar para confirmar pedido")).toBeVisible();

  await page.getByRole("button", { name: "Marcar como resuelto" }).click();
  await expect(page.getByRole("button", { name: "+ Programar seguimiento" })).toBeVisible();
});

test("reasignar una conversación a otro asesor", async ({ page }) => {
  await page.route("**/api/organizations/*/opportunities/opp-mine/history", (route) =>
    route.fulfill({
      json: { opportunity: MY_OPPORTUNITY, contact: CONTACT_MINE, follow_up: null, messages: [] },
    }),
  );
  await page.route("**/api/organizations/*/advisors", (route) =>
    route.fulfill({ json: [{ id: "advisor-2", full_name: "Andrea T." }] }),
  );

  let assignRequestBody: unknown;
  await page.route(
    "**/api/organizations/*/opportunities/opp-mine/assign-advisor",
    (route) => {
      assignRequestBody = route.request().postDataJSON();
      route.fulfill({ json: { ...MY_OPPORTUNITY, assigned_advisor_id: "advisor-2" } });
    },
  );

  await page.goto("/opportunities/opp-mine");
  await page.getByRole("button", { name: "Reasignar" }).click();
  await page.getByRole("button", { name: "Andrea T." }).click();

  await expect.poll(() => assignRequestBody).toEqual({ advisor_id: "advisor-2" });
  await expect(page).toHaveURL(/\/opportunities$/);
});

test("marcar una conversación como no leída llama al endpoint correcto", async ({ page }) => {
  await page.route("**/api/organizations/*/opportunities/opp-mine/history", (route) =>
    route.fulfill({
      json: { opportunity: MY_OPPORTUNITY, contact: CONTACT_MINE, follow_up: null, messages: [] },
    }),
  );

  let unreadRequestBody: unknown;
  await page.route("**/api/organizations/*/opportunities/opp-mine/unread", (route) => {
    unreadRequestBody = route.request().postDataJSON();
    route.fulfill({ json: { ...MY_OPPORTUNITY, unread_count: 1 } });
  });

  await page.goto("/opportunities/opp-mine");
  await page.getByRole("button", { name: "Más opciones" }).click();
  await page.getByRole("button", { name: "Marcar como no leída" }).click();

  await expect.poll(() => unreadRequestBody).toEqual({ unread: true });
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
