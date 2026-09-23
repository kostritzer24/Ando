import { expect, test } from "@playwright/test";

/**
 * Fase 8 (RF-06, RF-22, RF-26): grilla de horario (Dirección), horario
 * propio (docente) y calendario. Requiere `manage.py seed_demo`
 * (docente.demo asignado a Matemática, Segundo básico).
 */

async function entrarComo(page: import("@playwright/test").Page, usuario: string): Promise<void> {
  await page.goto("/ingresar");
  await page.getByLabel("Usuario").fill(usuario);
  await page.getByLabel("Contraseña").fill("CambiaEstaClave2026");
  await page.getByRole("button", { name: "Entrar" }).click();
}

test("Dirección arma el horario de un docente y lo puede quitar", async ({ page }) => {
  await entrarComo(page, "dir.demo");
  await expect(page).toHaveURL(/\/administrativo$/);

  await page.getByRole("link", { name: "Horarios" }).click();
  await expect(page.getByRole("heading", { name: "Horario" })).toBeVisible();

  // Los usuarios de siembra no tienen nombre/apellido cargados, así que
  // el selector muestra el username como respaldo (docente.demo).
  await page.getByLabel("Docente o tallerista").selectOption({ label: "docente.demo" });

  // Celda vacía: lunes, período 1 (primera fila, primera columna de datos).
  const primeraCelda = page.locator("table.horario-grid__tabla tbody tr").first().locator("td").first();
  await primeraCelda.getByRole("button", { name: "+" }).click();

  await expect(page.getByRole("heading", { name: "Agregar clase" })).toBeVisible();
  await page.getByRole("button", { name: "Guardar", exact: true }).click();

  await expect(page.getByRole("heading", { name: "Agregar clase" })).not.toBeVisible();
  await expect(primeraCelda.locator(".horario-grid__celda--ocupada")).toBeVisible();

  // La celda ocupada ya no ofrece "+" — el cruce queda evitado por diseño
  // (no se puede pedir una segunda clase en un espacio ya lleno).
  await expect(primeraCelda.getByRole("button", { name: "+" })).toHaveCount(0);

  page.once("dialog", (dialogo) => dialogo.accept());
  await primeraCelda.getByRole("button", { name: "Quitar" }).click();
  await expect(primeraCelda.getByRole("button", { name: "+" })).toBeVisible();
});

test("docente ve su propio horario después de que Dirección lo arma", async ({ page }) => {
  await entrarComo(page, "dir.demo");
  await expect(page).toHaveURL(/\/administrativo$/);
  await page.getByRole("link", { name: "Horarios" }).click();

  await page.getByLabel("Docente o tallerista").selectOption({ label: "docente.demo" });

  // Martes, período 2, para no chocar con la prueba anterior.
  const celda = page.locator("table.horario-grid__tabla tbody tr").nth(1).locator("td").nth(1);
  await celda.getByRole("button", { name: "+" }).click();
  await page.getByRole("button", { name: "Guardar", exact: true }).click();
  await expect(celda.locator(".horario-grid__celda--ocupada")).toBeVisible();

  await page.getByRole("button", { name: "Cerrar sesión" }).click();
  await entrarComo(page, "docente.demo");
  await expect(page).toHaveURL(/\/operativo$/);

  await page.getByRole("link", { name: "Mi horario" }).click();
  await expect(page.getByRole("heading", { name: "Mi horario" })).toBeVisible();
  await expect(page.locator(".mi-horario__celda")).toContainText("Matemática");
});

test("docente publica un evento propio y Dirección publica uno institucional", async ({ page }) => {
  await entrarComo(page, "docente.demo");
  await expect(page).toHaveURL(/\/operativo$/);

  await page.getByRole("link", { name: "Calendario" }).click();
  await expect(page.getByRole("heading", { name: "Calendario" })).toBeVisible();

  // Un docente no puede elegir "institucional" — el select ni lo ofrece
  // (solo el placeholder deshabilitado más la única opción real).
  await page.getByRole("button", { name: "Publicar evento" }).click();
  await expect(page.locator("#type option")).toHaveCount(2);
  await expect(page.locator("#type option", { hasText: "Institucional" })).toHaveCount(0);

  const tituloPropio = `Entrega de proyecto ${Date.now()}`;
  await page.locator('input[type="text"]').fill(tituloPropio);
  await page.locator('input[type="date"]').fill("2026-03-10");
  const horas = page.locator('input[type="time"]');
  await horas.nth(0).fill("09:00");
  await horas.nth(1).fill("10:00");
  await page.getByRole("button", { name: "Guardar", exact: true }).click();

  const filaPropia = page.locator("tr", { hasText: tituloPropio });
  await expect(filaPropia).toBeVisible();
  await expect(filaPropia.getByRole("button", { name: "Editar" })).toBeVisible();
  await expect(filaPropia.getByRole("button", { name: "Eliminar" })).toBeVisible();

  await page.getByRole("button", { name: "Cerrar sesión" }).click();
  await entrarComo(page, "dir.demo");
  await expect(page).toHaveURL(/\/administrativo$/);
  await page.getByRole("link", { name: "Calendario" }).click();

  const tituloInstitucional = `Suspensión de labores ${Date.now()}`;
  await page.getByRole("button", { name: "Publicar evento" }).click();
  await page.getByLabel("Tipo").selectOption({ label: "Institucional" });
  await page.locator('input[type="text"]').fill(tituloInstitucional);
  await page.locator('input[type="date"]').fill("2026-03-15");
  const horasDireccion = page.locator('input[type="time"]');
  await horasDireccion.nth(0).fill("08:00");
  await horasDireccion.nth(1).fill("08:40");
  await page.getByRole("button", { name: "Guardar", exact: true }).click();

  await expect(page.locator("tr", { hasText: tituloInstitucional })).toBeVisible();
  // Dirección puede editar/eliminar también el evento que publicó el docente.
  await expect(page.locator("tr", { hasText: tituloPropio }).getByRole("button", { name: "Editar" })).toBeVisible();

  await page.getByRole("button", { name: "Cerrar sesión" }).click();
  await entrarComo(page, "docente.demo");
  await page.getByRole("link", { name: "Calendario" }).click();

  // El aviso institucional es visible, pero sin botones de editar/eliminar.
  const filaInstitucional = page.locator("tr", { hasText: tituloInstitucional });
  await expect(filaInstitucional).toBeVisible();
  await expect(filaInstitucional.getByRole("button", { name: "Editar" })).toHaveCount(0);
});
