import { expect, test } from "@playwright/test";

import { menu } from "./utils";

/**
 * Fase 6 (RF-16, RF-12, RF-21): asistencia, justificaciones y plantilla
 * de talleres. Requiere `manage.py seed_demo` (docente.demo asignado a
 * Segundo básico, tallerista.demo al taller de panadería).
 */

async function entrarComo(page: import("@playwright/test").Page, usuario: string): Promise<void> {
  await page.goto("/ingresar");
  await page.getByLabel("Usuario").fill(usuario);
  await page.getByLabel("Contraseña").fill("CambiaEstaClave2026");
  await page.getByRole("button", { name: "Entrar" }).click();
}

test("docente toma asistencia de su sección y el estado se guarda solo", async ({ page }) => {
  await entrarComo(page, "docente.demo");
  await expect(page).toHaveURL(/\/operativo$/);

  await menu(page).getByRole("link", { name: "Asistencia" }).click();
  await expect(page.getByRole("heading", { name: "Tomar asistencia" })).toBeVisible();

  const primeraFila = page.locator(".tomar-asistencia__fila").first();
  await primeraFila.getByRole("button", { name: "Presente" }).click();
  await expect(primeraFila.getByRole("button", { name: "Presente" })).toHaveClass(/--activo/);

  const segundaFila = page.locator(".tomar-asistencia__fila").nth(1);
  await segundaFila.getByRole("button", { name: "Ausente" }).click();
  await expect(segundaFila.getByRole("button", { name: "Ausente" })).toHaveClass(/--activo/);

  // Recargar la página simula "volver más tarde" — HU-16.
  await page.reload();
  await expect(page.locator(".tomar-asistencia__fila").first().getByRole("button", { name: "Presente" })).toHaveClass(/--activo/);
  await expect(page.locator(".tomar-asistencia__fila").nth(1).getByRole("button", { name: "Ausente" })).toHaveClass(/--activo/);

  // Corregir un estado ya guardado (PATCH, no un segundo POST).
  await page.locator(".tomar-asistencia__fila").nth(1).getByRole("button", { name: "Presente" }).click();
  await expect(page.locator(".tomar-asistencia__fila").nth(1).getByRole("button", { name: "Presente" })).toHaveClass(/--activo/);
});

test("docente registra una justificación y Dirección la resuelve", async ({ page }) => {
  await entrarComo(page, "docente.demo");
  await expect(page).toHaveURL(/\/operativo$/);
  await menu(page).getByRole("link", { name: "Asistencia" }).click();
  await page.locator(".tomar-asistencia__fila").first().getByRole("button", { name: "Ausente" }).click();
  await expect(page.locator(".tomar-asistencia__fila").first().getByRole("button", { name: "Ausente" })).toHaveClass(/--activo/);

  await menu(page).getByRole("link", { name: "Justificaciones" }).click();
  await page.getByRole("button", { name: "Registrar justificación" }).click();
  await page.getByLabel("Falta a justificar").selectOption({ index: 1 });
  await page.getByLabel("Tipo de justificación").selectOption({ index: 1 });
  await page.locator("#reason_detail").fill("Cita médica.");
  await page.getByRole("button", { name: "Guardar", exact: true }).click();

  await expect(page.locator("tr", { hasText: "pendiente" })).toBeVisible();

  await page.getByRole("button", { name: "Cerrar sesión" }).click();
  await entrarComo(page, "dir.demo");
  await expect(page).toHaveURL(/\/administrativo$/);
  await menu(page).getByRole("link", { name: "Justificaciones" }).click();

  const fila = page.locator("tr", { hasText: "pendiente" }).first();
  await fila.getByRole("button", { name: "Aprobar" }).click();
  await expect(page.locator("tr", { hasText: "pendiente" })).toHaveCount(0);
});

test("tallerista descarga y sube la plantilla de asistencia de su taller", async ({ page }) => {
  await entrarComo(page, "tallerista.demo");
  await expect(page).toHaveURL(/\/operativo$/);

  await menu(page).getByRole("link", { name: "Plantilla de talleres" }).click();
  await expect(page.getByRole("heading", { name: "Plantilla de asistencia de talleres" })).toBeVisible();

  const [descarga] = await Promise.all([
    page.waitForEvent("download"),
    page.getByRole("button", { name: "Descargar plantilla" }).click(),
  ]);
  expect(descarga.suggestedFilename()).toMatch(/\.xlsx$/);
});
