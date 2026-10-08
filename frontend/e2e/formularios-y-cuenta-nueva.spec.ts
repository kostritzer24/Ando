import { expect, test } from "@playwright/test";

/**
 * Ronda de pruebas: B-010 (el formulario de inscripción no mostraba por qué
 * no guardaba) y B-019 (una familia sin estudiantes vinculados veía un
 * spinner infinito). Requiere `manage.py seed_demo`.
 */

async function entrarComo(page: import("@playwright/test").Page, usuario: string): Promise<void> {
  await page.goto("/ingresar");
  await page.getByLabel("Usuario").fill(usuario);
  await page.getByLabel("Contraseña").fill("CambiaEstaClave2026");
  await page.getByRole("button", { name: "Entrar" }).click();
}

test("inscribir sin datos muestra dentro del formulario qué falta", async ({ page }) => {
  await entrarComo(page, "dir.demo");
  await expect(page).toHaveURL(/\/administrativo/);
  await page.goto("/administrativo/estudiantes");
  await page.getByRole("button", { name: /Inscribir/ }).first().click();

  const modal = page.getByRole("dialog");
  await modal.getByRole("button", { name: "Inscribir" }).click();

  await expect(modal.getByRole("alert")).toContainText(/Nombres|Apellidos|Fecha de nacimiento/);
});

test("una familia sin estudiantes vinculados ve un mensaje y no un cargando infinito", async ({ page }) => {
  await page.route("**/api/v1/students/**", (ruta) =>
    ruta.fulfill({ json: { count: 0, next: null, previous: null, results: [] } }),
  );
  await page.route("**/api/v1/enrollments/**", (ruta) =>
    ruta.fulfill({ json: { count: 0, next: null, previous: null, results: [] } }),
  );
  await entrarComo(page, "familia.demo");
  await expect(page).toHaveURL(/\/portal/);

  await expect(page.getByText("Aún no hay estudiantes vinculados a tu cuenta")).toBeVisible();
});
