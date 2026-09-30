import { expect, test } from "@playwright/test";

import { menu } from "./utils";

/**
 * Fase 7 (RF-17 a RF-20, RF-23, RF-10): diseñar unidad, capturar notas,
 * plantilla de calificaciones, solicitudes de modificación. Requiere
 * `manage.py seed_demo` (docente.demo asignado a Matemática, Segundo
 * básico).
 */

async function entrarComo(page: import("@playwright/test").Page, usuario: string): Promise<void> {
  await page.goto("/ingresar");
  await page.getByLabel("Usuario").fill(usuario);
  await page.getByLabel("Contraseña").fill("CambiaEstaClave2026");
  await page.getByRole("button", { name: "Entrar" }).click();
}

test("docente diseña una unidad y ve el total de puntos en vivo", async ({ page }) => {
  await entrarComo(page, "docente.demo");
  await expect(page).toHaveURL(/\/operativo$/);

  await menu(page).getByRole("link", { name: "Diseñar unidad" }).click();
  await expect(page.getByRole("heading", { name: "Diseñar la unidad" })).toBeVisible();

  await page.getByRole("button", { name: "Agregar actividad" }).click();
  await page.getByLabel("Nombre de la actividad").fill("Prueba corta 1");
  await page.getByLabel("Tipo").selectOption({ index: 1 });
  await page.getByLabel("Punteo máximo").fill("10");
  await page.getByLabel("Fecha de entrega").fill("2026-02-01");
  await page.getByRole("button", { name: "Guardar", exact: true }).click();

  await expect(page.getByText("10 de 100 puntos usados")).toBeVisible();
  await expect(page.locator("tr", { hasText: "Prueba corta 1" })).toBeVisible();
});

test("docente captura una nota, solicita una corrección y Dirección la aprueba", async ({ page }) => {
  await entrarComo(page, "docente.demo");
  await expect(page).toHaveURL(/\/operativo$/);

  // Esta prueba no depende de la anterior: crea su propia actividad.
  await menu(page).getByRole("link", { name: "Diseñar unidad" }).click();
  await page.getByRole("button", { name: "Agregar actividad" }).click();
  const nombreActividad = `Tarea de prueba ${Date.now()}`;
  await page.getByLabel("Nombre de la actividad").fill(nombreActividad);
  await page.getByLabel("Tipo").selectOption({ index: 1 });
  await page.getByLabel("Punteo máximo").fill("10");
  await page.getByLabel("Fecha de entrega").fill("2026-02-01");
  await page.getByRole("button", { name: "Guardar", exact: true }).click();
  await expect(page.locator("tr", { hasText: nombreActividad })).toBeVisible();

  await menu(page).getByRole("link", { name: "Capturar notas" }).click();
  await expect(page.getByRole("heading", { name: "Capturar notas" })).toBeVisible();
  // La lista de actividades se carga de forma asíncrona después de elegir
  // la unidad por omisión — se espera a que la opción exista antes de leerla.
  const opcionNueva = page.locator("#activity option", { hasText: nombreActividad });
  await expect(opcionNueva).toBeAttached();
  const etiquetaActividad = await opcionNueva.innerText();
  await page.getByLabel("Actividad").selectOption({ label: etiquetaActividad });

  const primeraFila = page.locator(".capturar-notas__fila").first();
  // El navegador solo dispara "change" en un <input type="number"> al
  // perder el foco, no con fill() solo — de ahí el Tab.
  await primeraFila.locator(".capturar-notas__input").fill("8");
  await primeraFila.locator(".capturar-notas__input").press("Tab");

  await expect(primeraFila.locator(".capturar-notas__nota-vigente")).toContainText("8");

  // El punteo real ya no se puede editar directo — hay que pedir corrección.
  await primeraFila.getByRole("button", { name: "Solicitar corrección" }).click();
  await page.getByLabel("Nota propuesta").fill("9");
  await page.locator("#reason").fill("Se recalificó un ejercicio.");
  await page.getByRole("button", { name: "Enviar solicitud" }).click();

  await menu(page).getByRole("link", { name: "Modificaciones" }).click();
  await expect(page.getByRole("heading", { name: "Mis solicitudes de modificación" })).toBeVisible();
  await expect(page.locator("tr", { hasText: "pendiente" })).toBeVisible();

  await page.getByRole("button", { name: "Cerrar sesión" }).click();
  await entrarComo(page, "dir.demo");
  await expect(page).toHaveURL(/\/administrativo$/);
  await menu(page).getByRole("link", { name: "Modificaciones de notas" }).click();
  await expect(page.getByRole("heading", { name: "Solicitudes de modificación" })).toBeVisible();

  const fila = page.locator("tr", { hasText: "pendiente" }).first();
  await fila.getByRole("button", { name: "Aprobar" }).click();
  await expect(page.locator("tr", { hasText: "pendiente" })).toHaveCount(0);
});

test("docente descarga la plantilla de calificaciones de su unidad", async ({ page }) => {
  await entrarComo(page, "docente.demo");
  await expect(page).toHaveURL(/\/operativo$/);

  await menu(page).getByRole("link", { name: "Plantilla de notas" }).click();
  await expect(page.getByRole("heading", { name: "Plantilla de calificaciones" })).toBeVisible();

  const [descarga] = await Promise.all([
    page.waitForEvent("download"),
    page.getByRole("button", { name: "Descargar plantilla" }).click(),
  ]);
  expect(descarga.suggestedFilename()).toMatch(/\.xlsx$/);
});
