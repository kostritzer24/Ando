import { expect, test } from "@playwright/test";

/**
 * Uno de los seis flujos de extremo a punta de la sección 16 del prompt
 * maestro. Requiere el backend local corriendo con la semilla de la
 * Fase 3 (`cd backend && python manage.py seed_fase3`), que crea
 * `dir.demo` / `CambiaEstaClave2026` con el rol Dirección.
 */
test("una persona con rol Dirección entra y llega al portal administrativo", async ({ page }) => {
  await page.goto("/ingresar");

  await page.getByLabel("Usuario").fill("dir.demo");
  await page.getByLabel("Contraseña").fill("CambiaEstaClave2026");
  await page.getByRole("button", { name: "Entrar" }).click();

  await expect(page).toHaveURL(/\/administrativo$/);
  await expect(page.getByText("Portal administrativo")).toBeVisible();
  await expect(page.getByRole("heading", { level: 1, name: /^Hola/ })).toBeVisible();
});

test("una contraseña incorrecta muestra un error y no entra", async ({ page }) => {
  await page.goto("/ingresar");

  await page.getByLabel("Usuario").fill("dir.demo");
  await page.getByLabel("Contraseña").fill("una-contraseña-que-no-es");
  await page.getByRole("button", { name: "Entrar" }).click();

  await expect(page.getByRole("alert")).toContainText("incorrectos");
  await expect(page).toHaveURL(/\/ingresar$/);
});
