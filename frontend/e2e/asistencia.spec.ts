import { expect, test } from "@playwright/test";

import { elegirPrimeraDelBuscador, menu } from "./utils";

/**
 * Fase 6 (RF-16, RF-12): asistencia y justificaciones. Dirección marca
 * la jornada, el docente solo la consulta y el tallerista marca su taller. Requiere `manage.py seed_demo` (docente.demo asignado a
 * Segundo básico, tallerista.demo al taller de panadería).
 */

async function entrarComo(page: import("@playwright/test").Page, usuario: string): Promise<void> {
  await page.goto("/ingresar");
  await page.getByLabel("Usuario").fill(usuario);
  await page.getByLabel("Contraseña").fill("CambiaEstaClave2026");
  await page.getByRole("button", { name: "Entrar" }).click();
}

test("Dirección deja a todos presentes y corrige a quien faltó", async ({ page }) => {
  await entrarComo(page, "dir.demo");
  await expect(page).toHaveURL(/\/administrativo$/);

  await menu(page).getByRole("link", { name: "Asistencia" }).click();
  await expect(page.getByRole("heading", { name: "Tomar asistencia" })).toBeVisible();
  // Segundo básico es la sección con estudiantes en la siembra.
  await page.getByLabel("Sección").selectOption({ label: "Segundo básico" });

  await page.getByRole("button", { name: "Marcar presentes a los pendientes de esta sección" }).click();
  const primeraFila = page.locator(".tomar-asistencia__fila").first();
  await expect(primeraFila.getByRole("button", { name: "Presente" })).toHaveClass(/--activo/);

  // Solo se corrige a quien faltó (PATCH sobre lo ya marcado).
  await primeraFila.getByRole("button", { name: "Ausente" }).click();
  await expect(primeraFila.getByRole("button", { name: "Ausente" })).toHaveClass(/--activo/);

  await page.reload();
  await page.getByLabel("Sección").selectOption({ label: "Segundo básico" });
  await expect(page.locator(".tomar-asistencia__fila").first().getByRole("button", { name: "Ausente" })).toHaveClass(/--activo/);
});

test("el docente consulta la asistencia pero no puede marcarla", async ({ page }) => {
  await entrarComo(page, "docente.demo");
  await expect(page).toHaveURL(/\/operativo$/);
  await menu(page).getByRole("link", { name: "Asistencia" }).click();
  await expect(page.getByRole("heading", { name: "Asistencia", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Marcar presentes a los pendientes de esta sección" })).toHaveCount(0);
  await expect(page.locator(".tomar-asistencia__fila").first().getByRole("button", { name: "Presente" })).toBeDisabled();
});

test("Dirección registra una justificación y la resuelve", async ({ page }) => {
  await entrarComo(page, "dir.demo");
  await expect(page).toHaveURL(/\/administrativo$/);
  await menu(page).getByRole("link", { name: "Asistencia" }).click();
  await page.getByLabel("Sección").selectOption({ label: "Segundo básico" });
  await page.locator(".tomar-asistencia__fila").first().getByRole("button", { name: "Ausente" }).click();
  await expect(page.locator(".tomar-asistencia__fila").first().getByRole("button", { name: "Ausente" })).toHaveClass(/--activo/);

  await menu(page).getByRole("link", { name: "Justificaciones" }).click();
  await page.getByRole("button", { name: "Registrar justificación" }).click();
  await elegirPrimeraDelBuscador(page, "Falta a justificar");
  await page.getByLabel("Tipo de justificación").selectOption({ index: 1 });
  await page.locator("#reason_detail").fill("Cita médica.");
  await page.getByRole("button", { name: "Guardar", exact: true }).click();

  const fila = page.locator("tr", { hasText: "pendiente" }).first();
  await expect(fila).toBeVisible();
  await fila.getByRole("button", { name: "Aprobar" }).click();
  await expect(page.locator("tr", { hasText: "pendiente" })).toHaveCount(0);
});

test("el tallerista pasa lista de su taller como una clase normal", async ({ page }) => {
  await entrarComo(page, "tallerista.demo");
  await expect(page).toHaveURL(/\/operativo$/);

  await menu(page).getByRole("link", { name: "Asistencia" }).click();
  await expect(page.getByRole("heading", { name: "Tomar asistencia" })).toBeVisible();
  await expect(menu(page).getByRole("link", { name: "Plantilla de talleres" })).toHaveCount(0);

  // Si ya se marcó en una corrida anterior no queda nada pendiente y el botón se apaga.
  const marcarTodos = page.getByRole("button", { name: "Marcar presentes a los pendientes de esta sección" });
  await expect(marcarTodos).toBeVisible();
  if (await marcarTodos.isEnabled()) await marcarTodos.click();
  await expect(page.locator(".tomar-asistencia__fila").first().getByRole("button", { name: "Presente" })).toHaveClass(/--activo/);
});
