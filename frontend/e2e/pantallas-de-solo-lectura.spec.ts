import { expect, test } from "@playwright/test";

/**
 * Ronda de pruebas (A-005): Coordinación y Encargado de pagos abren
 * pantallas que su rol puede ver aunque algunos datos auxiliares (lista de
 * usuarios, secciones, tipos de documento) queden fuera de su alcance.
 * Antes la pantalla entera se reemplazaba por "No se pudo cargar".
 * Requiere `manage.py seed_demo`.
 */

async function entrarComo(page: import("@playwright/test").Page, usuario: string): Promise<void> {
  await page.goto("/ingresar");
  await page.getByLabel("Usuario").fill(usuario);
  await page.getByLabel("Contraseña").fill("CambiaEstaClave2026");
  await page.getByRole("button", { name: "Entrar" }).click();
  await expect(page).toHaveURL(/\/administrativo/);
}

test("Coordinación ve asignaciones y horarios sin errores de carga", async ({ page }) => {
  await entrarComo(page, "coord.demo");

  await page.goto("/administrativo/asignaciones");
  await expect(page.getByRole("heading", { name: /Asignaciones de docentes/ })).toBeVisible();
  await expect(page.getByText("No se pudo cargar")).toHaveCount(0);
  // El nombre sale de la propia asignación, aunque Coordinación no vea /users/.
  await expect(page.getByText("docente.demo").or(page.getByText(/Docente/)).first()).toBeVisible();

  await page.goto("/administrativo/horarios");
  await expect(page.getByRole("heading", { name: "Horario" })).toBeVisible();
  await expect(page.getByText("No se pudo cargar")).toHaveCount(0);
});

test("Encargado de pagos ve estudiantes y documentos sin errores de carga", async ({ page }) => {
  await entrarComo(page, "pagos.demo");

  await page.goto("/administrativo/estudiantes");
  await expect(page.getByRole("heading", { name: "Estudiantes" })).toBeVisible();
  await expect(page.getByText("No se pudo cargar")).toHaveCount(0);

  await page.goto("/administrativo/documentos");
  await expect(page.getByText("No se pudo cargar")).toHaveCount(0);
});
