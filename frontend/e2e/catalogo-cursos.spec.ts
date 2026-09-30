import { expect, test } from "@playwright/test";

import { menu } from "./utils";

/**
 * Fase 4 (RF-02): CRUD de datos maestros. Requiere el backend local con
 * `manage.py seed_demo` corrido (crea `dir.demo` / `CambiaEstaClave2026`).
 */
test.beforeEach(async ({ page }) => {
  await page.goto("/ingresar");
  await page.getByLabel("Usuario").fill("dir.demo");
  await page.getByLabel("Contraseña").fill("CambiaEstaClave2026");
  await page.getByRole("button", { name: "Entrar" }).click();
  await expect(page).toHaveURL(/\/administrativo$/);
});

test("Dirección crea, edita y da de baja un curso desde el catálogo", async ({ page }) => {
  await menu(page).getByRole("link", { name: "Datos maestros" }).click();
  await page.getByRole("link", { name: "Cursos" }).click();
  await expect(page.getByRole("heading", { name: "Cursos" })).toBeVisible();

  const nombreCurso = `Curso de prueba ${Date.now()}`;

  await page.getByRole("button", { name: "Agregar curso" }).click();
  await page.getByLabel("Nombre").fill(nombreCurso);
  await page.getByLabel("Tipo").selectOption("academico");
  await page.getByRole("button", { name: "Guardar" }).click();

  const fila = page.locator("tr", { hasText: nombreCurso });
  await expect(fila).toBeVisible();
  await expect(fila).toContainText("Académico");

  await fila.getByRole("button", { name: "Editar" }).click();
  await page.getByLabel("Tipo").selectOption("taller");
  await page.getByRole("button", { name: "Guardar" }).click();
  await expect(fila).toContainText("Taller");

  // HU-02: nada se borra de verdad — "dar de baja" solo pone is_active en
  // false, el registro se queda en la lista (para poder reactivarlo), así
  // que por omisión se esconde y hay que pedir verlo explícitamente.
  await fila.getByRole("button", { name: "Dar de baja" }).click();
  await page.getByRole("dialog").getByRole("button", { name: "Dar de baja" }).click();
  await expect(page.locator("tr", { hasText: nombreCurso })).toHaveCount(0);

  await page.getByLabel("Mostrar los dados de baja").check();
  await expect(fila).toContainText("Dado de baja");

  await fila.getByRole("button", { name: "Reactivar" }).click();
  await page.getByLabel("Mostrar los dados de baja").uncheck();
  await expect(fila).toBeVisible();
});

test("Coordinación ve el catálogo pero no tiene botones de edición", async ({ page }) => {
  // El beforeEach ya entró como dir.demo — hay que cerrar esa sesión
  // antes, si no la redirección de /ingresar con sesión activa (la
  // sección de "sesión persistente") manda de vuelta al portal sin
  // mostrar el formulario para entrar como otra persona.
  await page.getByRole("button", { name: "Cerrar sesión" }).click();
  await expect(page).toHaveURL(/\/ingresar$/);

  await page.getByLabel("Usuario").fill("coord.demo");
  await page.getByLabel("Contraseña").fill("CambiaEstaClave2026");
  await page.getByRole("button", { name: "Entrar" }).click();
  await expect(page).toHaveURL(/\/administrativo$/);

  await page.goto("/administrativo/catalogo/cursos");
  await expect(page.getByRole("heading", { name: "Cursos" })).toBeVisible();
  await expect(page.getByRole("button", { name: /^Agregar/ })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Editar" })).toHaveCount(0);
});
