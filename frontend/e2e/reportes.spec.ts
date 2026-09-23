import { expect, test } from "@playwright/test";

/**
 * Fase 12 (RF-15, sección 11): los ocho reportes institucionales con
 * filtros y descarga en PDF, más las métricas del estudio. Requiere
 * `manage.py seed_demo` (Ana Lucía Con Morales, ES003, sin ningún pago
 * — insolvente desde la siembra).
 */

async function entrarComo(page: import("@playwright/test").Page, usuario: string): Promise<void> {
  await page.goto("/ingresar");
  await page.getByLabel("Usuario").fill(usuario);
  await page.getByLabel("Contraseña").fill("CambiaEstaClave2026");
  await page.getByRole("button", { name: "Entrar" }).click();
}

test("Dirección consulta reportes institucionales, cambia de reporte y descarga el PDF", async ({ page }) => {
  await entrarComo(page, "dir.demo");
  await expect(page).toHaveURL(/\/administrativo$/);

  await page.getByRole("link", { name: "Reportes", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Reportes institucionales" })).toBeVisible();

  // Por omisión carga "Consolidado de notas" — cambiar a insolventes.
  await page.getByLabel("Reporte").selectOption({ label: "Estudiantes insolventes" });
  await page.getByRole("button", { name: "Consultar" }).click();
  await expect(page.locator("tr", { hasText: "Ana Lucía Con Morales" })).toBeVisible();

  const descarga = page.waitForEvent("download");
  await page.getByRole("button", { name: "Descargar PDF" }).click();
  await descarga;

  // Estudiantes inscritos: las 4 personas de la siembra (María aparece
  // dos veces — sección académica y taller).
  await page.getByLabel("Reporte").selectOption({ label: "Estudiantes inscritos" });
  await page.getByRole("button", { name: "Consultar" }).click();
  await expect(page.locator("tbody tr")).toHaveCount(5);

  await page.getByRole("link", { name: "Métricas" }).click();
  await expect(page.getByRole("heading", { name: "Métricas del estudio" })).toBeVisible();
  await expect(page.getByText("Procesos administrativos gestionados por el sistema")).toBeVisible();
  await expect(page.getByText("Encargados que consultaron el portal esta semana")).toBeVisible();
});

test("Encargado de pagos descarga el reporte de insolventes desde Pagos, pero no ve el menú de Reportes", async ({
  page,
}) => {
  await entrarComo(page, "pagos.demo");
  await expect(page).toHaveURL(/\/administrativo$/);

  await expect(page.getByRole("link", { name: "Reportes", exact: true })).toHaveCount(0);
  await expect(page.getByRole("link", { name: "Métricas" })).toHaveCount(0);

  await page.getByRole("link", { name: "Pagos y solvencia" }).click();
  const descarga = page.waitForEvent("download");
  await page.getByRole("button", { name: "Reporte de estudiantes insolventes" }).click();
  await descarga;
});

test("un docente no llega a los reportes institucionales", async ({ page }) => {
  await entrarComo(page, "docente.demo");
  await expect(page).toHaveURL(/\/operativo$/);

  await expect(page.getByRole("link", { name: "Reportes", exact: true })).toHaveCount(0);
});
