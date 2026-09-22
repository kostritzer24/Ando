import { expect, test } from "@playwright/test";

/**
 * Fase 4 (RF-02): las dos pantallas de catálogo con lógica propia —
 * Ciclos con sus unidades anidadas, y Secciones con el selector de
 * maestro guía. Requiere `manage.py seed_demo` (crea el ciclo 2026 con
 * sus 4 unidades, 7 secciones y `guia.demo` con rol "Docente con
 * sección a cargo").
 */
test.beforeEach(async ({ page }) => {
  await page.goto("/ingresar");
  await page.getByLabel("Usuario").fill("dir.demo");
  await page.getByLabel("Contraseña").fill("CambiaEstaClave2026");
  await page.getByRole("button", { name: "Entrar" }).click();
  await expect(page).toHaveURL(/\/administrativo$/);
});

test("Dirección agrega una unidad a un ciclo existente y ve las fechas calculadas", async ({ page }) => {
  await page.goto("/administrativo/catalogo/ciclos");
  await expect(page.getByRole("heading", { name: "Ciclos escolares y unidades" })).toBeVisible();

  const filaCiclo = page.locator("tr", { hasText: "2026" });
  await filaCiclo.getByRole("button", { name: "Ver unidades" }).click();
  await expect(page.getByRole("heading", { name: "Unidades del ciclo 2026" })).toBeVisible();

  const tablaUnidades = page.locator("table").nth(1);
  // seed_demo crea exactamente 4 unidades para el ciclo 2026 — se espera
  // a que la carga asíncrona termine antes de contar filas, si no la
  // lectura puede ganarle a la petición y contar 0.
  await expect(tablaUnidades.locator("tbody tr")).toHaveCount(4);

  await page.getByRole("button", { name: "Agregar unidad" }).click();
  await page.getByLabel("Número de unidad").fill("5");
  await page.getByLabel("Fecha de inicio").fill("2026-08-17");
  await page.getByLabel("Fecha de cierre").fill("2026-10-09");
  await page.getByRole("button", { name: "Guardar" }).click();

  await expect(tablaUnidades.locator("tbody tr")).toHaveCount(5);
  // RN-10: la fecha de entrega de notas y de habilitación del boletín las
  // calcula el sistema — no se piden en el formulario y sí aparecen en la
  // tabla resultante.
  await expect(tablaUnidades).toContainText("2026-10-24"); // grades_due_date: +15 días
});

test("Dirección crea una sección académica con maestro guía", async ({ page }) => {
  await page.goto("/administrativo/catalogo/secciones");
  await expect(page.getByRole("heading", { name: "Secciones" })).toBeVisible();

  await page.getByRole("button", { name: "Agregar sección" }).click();
  await page.getByLabel("Grado").fill("Sexto bachillerato");
  await page.getByLabel("Letra").fill("");
  await page.getByLabel("Tipo").selectOption("academica");
  await expect(page.getByLabel("Maestro guía")).toBeVisible();
  await page.getByLabel("Maestro guía").selectOption({ index: 1 });
  await page.getByRole("button", { name: "Guardar" }).click();

  await expect(page.locator("tr", { hasText: "Sexto bachillerato" })).toBeVisible();
});

test("el selector de maestro guía se esconde para una sección de taller", async ({ page }) => {
  await page.goto("/administrativo/catalogo/secciones");
  await page.getByRole("button", { name: "Agregar sección" }).click();
  await page.getByLabel("Tipo").selectOption("taller");
  await expect(page.getByLabel("Maestro guía")).toHaveCount(0);
});
