import { expect, test } from "@playwright/test";

/**
 * El token de acceso vive solo en memoria (sección 14.1) — recargar la
 * página, o entrar por un enlace directo, tiene que reconstruir la
 * sesión desde la cookie HttpOnly del token de refresco (GET /auth/me/),
 * no mandar a la persona a iniciar sesión de nuevo cada vez.
 */
test("recargar la página no cierra la sesión", async ({ page }) => {
  await page.goto("/ingresar");
  await page.getByLabel("Usuario").fill("dir.demo");
  await page.getByLabel("Contraseña").fill("CambiaEstaClave2026");
  await page.getByRole("button", { name: "Entrar" }).click();
  await expect(page).toHaveURL(/\/administrativo$/);

  await page.reload();

  await expect(page).toHaveURL(/\/administrativo$/);
  await expect(page.getByText("Portal administrativo")).toBeVisible();
  await expect(page.getByRole("heading", { level: 1, name: /^Hola/ })).toBeVisible();
});

test("entrar por un enlace directo a una pantalla interna reconstruye la sesión", async ({ page }) => {
  await page.goto("/ingresar");
  await page.getByLabel("Usuario").fill("dir.demo");
  await page.getByLabel("Contraseña").fill("CambiaEstaClave2026");
  await page.getByRole("button", { name: "Entrar" }).click();
  await expect(page).toHaveURL(/\/administrativo$/);

  // Navegación de página completa, no un push del router — simula abrir
  // un enlace guardado o escribir la URL directamente.
  await page.goto("/administrativo/catalogo/cursos");

  await expect(page.getByRole("heading", { name: "Cursos" })).toBeVisible();
});

test("sin sesión, entrar por un enlace directo manda a /ingresar", async ({ page, context }) => {
  await context.clearCookies();
  await page.goto("/administrativo/catalogo/cursos");
  await expect(page).toHaveURL(/\/ingresar$/);
});

test("entrar a /ingresar con sesión activa redirige al portal, no muestra el formulario de nuevo", async ({
  page,
}) => {
  await page.goto("/ingresar");
  await page.getByLabel("Usuario").fill("dir.demo");
  await page.getByLabel("Contraseña").fill("CambiaEstaClave2026");
  await page.getByRole("button", { name: "Entrar" }).click();
  await expect(page).toHaveURL(/\/administrativo$/);

  await page.goto("/ingresar");

  await expect(page).toHaveURL(/\/administrativo$/);
});
