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

test("Dirección crea un ciclo, agrega una unidad y ve las fechas calculadas; las fechas incoherentes se rechazan", async ({ page }) => {
  await page.goto("/administrativo/catalogo/ciclos");
  await expect(page.getByRole("heading", { name: "Ciclos escolares y unidades" })).toBeVisible();

  // Un año propio de la prueba, para no chocar con el ciclo sembrado ni con corridas anteriores.
  const anio = 2100 + Math.floor(Math.random() * 800);
  await page.getByRole("button", { name: "Agregar ciclo" }).click();
  await page.getByLabel("Año").fill(String(anio));
  await page.getByLabel("Fecha de inicio").fill(`${anio}-01-12`);
  await page.getByLabel("Fecha de cierre").fill(`${anio}-10-30`);
  await page.getByRole("button", { name: "Guardar" }).click();

  const filaCiclo = page.locator("tr", { hasText: String(anio) });
  await filaCiclo.getByRole("button", { name: "Ver unidades" }).click();
  await expect(page.getByRole("heading", { name: `Unidades del ciclo ${anio}` })).toBeVisible();

  // Fechas fuera del ciclo: el servidor las rechaza y el motivo se ve en el diálogo.
  await page.getByRole("button", { name: "Agregar unidad" }).click();
  await page.getByLabel("Número de unidad").fill("1");
  await page.getByLabel("Fecha de inicio").fill(`${anio - 1}-12-01`);
  await page.getByLabel("Fecha de cierre").fill(`${anio}-03-31`);
  await page.getByRole("button", { name: "Guardar" }).click();
  await expect(page.getByRole("dialog").getByRole("alert")).toContainText("dentro del ciclo");

  await page.getByLabel("Fecha de inicio").fill(`${anio}-01-12`);
  await page.getByRole("button", { name: "Guardar" }).click();

  const tablaUnidades = page.locator("table").nth(1);
  await expect(tablaUnidades.locator("tbody tr")).toHaveCount(1);
  // La fecha de entrega de notas (+15 días del cierre) la calcula el sistema.
  await expect(tablaUnidades).toContainText(`15/04/${anio}`);
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
