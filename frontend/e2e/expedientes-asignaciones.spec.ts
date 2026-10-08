import { expect, test } from "@playwright/test";

import { menu } from "./utils";

/**
 * Fase 5 (RF-03, RF-04, RF-05): expedientes, encargados y asignaciones.
 * Requiere `manage.py seed_demo` (secciones, cursos, ES001..ES004,
 * docente.demo/guia.demo/tallerista.demo con sus asignaciones).
 */
test.beforeEach(async ({ page }) => {
  await page.goto("/ingresar");
  await page.getByLabel("Usuario").fill("dir.demo");
  await page.getByLabel("Contraseña").fill("CambiaEstaClave2026");
  await page.getByRole("button", { name: "Entrar" }).click();
  await expect(page).toHaveURL(/\/administrativo$/);
});

test("Dirección inscribe un estudiante y el sistema le asigna el código", async ({ page }) => {
  await menu(page).getByRole("link", { name: "Estudiantes", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Estudiantes" })).toBeVisible();

  await page.getByRole("button", { name: "Inscribir estudiante" }).click();
  await page.getByLabel("Nombres").fill("Estudiante");
  await page.getByLabel("Apellidos").fill(`Prueba ${Date.now()}`);
  await page.getByLabel("Fecha de nacimiento").fill("2012-04-10");
  await page.getByLabel("Sección").selectOption({ index: 1 });
  await page.getByRole("button", { name: "Inscribir", exact: true }).click();

  await expect(page.getByText(/Estudiante inscrito con el código/)).toBeVisible();
});

test("Dirección ve y edita el expediente general y los datos sensibles de un estudiante", async ({
  page,
}) => {
  await page.goto("/administrativo/estudiantes");
  const primeraFila = page.locator("tbody tr").first();
  await primeraFila.getByRole("button", { name: "Ver expediente" }).click();

  await expect(page.getByText(/Código interno:/)).toBeVisible();

  await page.getByLabel("Dirección").fill("Zona 1, Jocotenango");
  await page.getByRole("button", { name: "Guardar", exact: true }).click();

  await expect(page.getByRole("heading", { name: "Datos sensibles" })).toBeVisible();
  await page.getByLabel("Datos de salud").fill("Sin condiciones registradas.");
  await page.getByRole("button", { name: "Guardar datos sensibles" }).click();
});

test("Coordinación ve el expediente pero no puede editarlo ni ver datos sensibles", async ({
  page,
}) => {
  await page.getByRole("button", { name: "Cerrar sesión" }).click();
  await page.getByLabel("Usuario").fill("coord.demo");
  await page.getByLabel("Contraseña").fill("CambiaEstaClave2026");
  await page.getByRole("button", { name: "Entrar" }).click();
  await expect(page).toHaveURL(/\/administrativo$/);

  await page.goto("/administrativo/estudiantes");
  await page.locator("tbody tr").first().getByRole("button", { name: "Ver expediente" }).click();

  await expect(page.getByLabel("Nombres")).toBeDisabled();
  await expect(page.getByRole("button", { name: "Guardar" })).toHaveCount(0);
  await expect(page.getByText("Datos sensibles")).toHaveCount(0);
});

test("Dirección crea un encargado, lo vincula a un estudiante y lo desvincula", async ({ page }) => {
  await menu(page).getByRole("link", { name: "Encargados" }).click();
  await expect(page.getByRole("heading", { name: "Encargados" })).toBeVisible();

  const username = `familia.prueba.${Date.now()}`;
  await page.getByRole("button", { name: "Agregar encargado" }).click();
  await page.getByLabel("Usuario").fill(username);
  await page.getByLabel("Contraseña temporal").fill("Clave-Segura-2026");
  await page.getByLabel("Nombres").fill("Encargado");
  await page.getByLabel("Apellidos").fill("De Prueba");
  await page.getByRole("button", { name: "Guardar" }).click();

  const fila = page.locator("tr", { hasText: "Encargado De Prueba" });
  await expect(fila).toBeVisible();

  await fila.getByRole("button", { name: "Ver vínculos" }).click();
  await expect(page.getByText(/Estudiantes vinculados a Encargado De Prueba/)).toBeVisible();
  await expect(page.getByText("Sin vínculos todavía.")).toBeVisible();

  await page.locator("select").filter({ hasText: "Elige un estudiante" }).selectOption({ index: 1 });
  await page.getByPlaceholder("Parentesco (Madre, Padre, …)").fill("Tía");
  await page.getByRole("button", { name: "Vincular" }).click();

  await expect(page.getByText(/— Tía/)).toBeVisible();

  await page.getByRole("button", { name: "Desvincular" }).click();
  await expect(page.getByText("Sin vínculos todavía.")).toBeVisible();
});

test("Dirección asigna un docente a un curso académico y el selector filtra por tipo de sección", async ({
  page,
}) => {
  await menu(page).getByRole("link", { name: "Asignaciones" }).click();
  await expect(page.getByRole("heading", { name: "Asignaciones de docentes y talleristas" })).toBeVisible();

  await page.getByRole("button", { name: "Agregar asignación" }).click();
  // Tercero básico no tiene asignación todavía en la siembra de demo.
  await page.getByLabel("Sección").selectOption({ label: "Tercero básico" });
  await expect(page.getByLabel("Docente o tallerista")).toBeEnabled();
  const opcionesDocente = await page.getByLabel("Docente o tallerista").locator("option").allTextContents();
  expect(opcionesDocente).not.toContain("tallerista.demo");

  await page.getByLabel("Curso").selectOption({ index: 1 });
  await page.getByLabel("Docente o tallerista").selectOption({ index: 1 });
  await page.getByRole("button", { name: "Guardar" }).click();

  await expect(page.locator("tr", { hasText: "Tercero básico" })).toBeVisible();
});

test("el selector de docente filtra a Tallerista cuando la sección es de taller", async ({ page }) => {
  await page.goto("/administrativo/asignaciones");
  await page.getByRole("button", { name: "Agregar asignación" }).click();
  // allTextContents() no espera: primero, que la opción de taller exista.
  await expect(page.getByLabel("Sección").locator("option", { hasText: "(taller)" })).toHaveCount(1);
  const opcionesSeccion = await page.getByLabel("Sección").locator("option").allTextContents();
  const etiquetaTaller = opcionesSeccion.find((o) => o.includes("taller"));
  await page.getByLabel("Sección").selectOption({ label: etiquetaTaller });

  const opciones = await page.getByLabel("Curso").locator("option").allTextContents();
  expect(opciones.some((o) => o.toLowerCase().includes("panadería"))).toBe(true);
  expect(opciones.some((o) => o === "Matemática")).toBe(false);
});
