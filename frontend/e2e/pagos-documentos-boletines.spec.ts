import { expect, test } from "@playwright/test";

import { menu } from "./utils";

/**
 * Fase 9 (RF-07 a RF-09, RF-11, RF-14): registrar pagos y consultar
 * solvencia, emitir constancia de solvencia, emitir documentos generales
 * y bandeja de boletines (generar/aprobar/publicar). Requiere
 * `manage.py seed_demo` (María Ximena solvente, Juan Carlos becado, Ana
 * Lucía insolvente, Diego parcial — ver `seed_demo.py`).
 */

async function entrarComo(page: import("@playwright/test").Page, usuario: string): Promise<void> {
  await page.goto("/ingresar");
  await page.getByLabel("Usuario").fill(usuario);
  await page.getByLabel("Contraseña").fill("CambiaEstaClave2026");
  await page.getByRole("button", { name: "Entrar" }).click();
}

async function elegirEstudiante(
  page: import("@playwright/test").Page,
  idSelect: string,
  fragmentoNombre: string,
): Promise<void> {
  const opcionesLocator = page.locator(`#${idSelect} option`);
  await expect(opcionesLocator.nth(1)).toBeAttached();
  const opciones = await opcionesLocator.allTextContents();
  const indice = opciones.findIndex((o) => o.includes(fragmentoNombre));
  await page.locator(`#${idSelect}`).selectOption({ index: indice });
}

test("Encargado de pagos consulta solvencia, registra un pago y emite la constancia", async ({ page }) => {
  await entrarComo(page, "pagos.demo");
  await expect(page).toHaveURL(/\/administrativo$/);

  await menu(page).getByRole("link", { name: "Pagos y solvencia" }).click();
  await expect(page.getByRole("heading", { name: "Pagos y solvencia" })).toBeVisible();

  // María Ximena está al día (seed_demo la paga por completo).
  await elegirEstudiante(page, "inscripcion", "María Ximena");
  await expect(page.getByText("Al día con sus pagos.")).toBeVisible();
  const botonConstancia = page.getByRole("button", { name: "Emitir constancia de solvencia" });
  await expect(botonConstancia).toBeEnabled();

  const descarga = page.waitForEvent("download");
  await botonConstancia.click();
  const archivo = await descarga;
  expect(archivo.suggestedFilename()).toContain("constancia_solvencia");

  // Ana Lucía no tiene ningún pago registrado: insolvente, constancia bloqueada.
  await elegirEstudiante(page, "inscripcion", "Ana Lucía");
  await expect(page.getByText("No está solvente.")).toBeVisible();
  await expect(page.getByText("Meses pendientes:")).toBeVisible();
  await expect(page.getByRole("button", { name: "Emitir constancia de solvencia" })).toBeDisabled();

  const numeroRecibo = `E2E-${Date.now()}`;
  await page.getByLabel("Mes").selectOption({ label: "Enero" });
  await page.getByLabel("Año").fill("2026");
  await page.getByLabel("Año").press("Tab");
  await page.getByLabel("Monto (Q)").fill("150.00");
  await page.getByLabel("Monto (Q)").press("Tab");
  await page.getByLabel("Fecha de pago").fill("2026-01-05");
  await page.getByLabel("Número de recibo").fill(numeroRecibo);
  await page.getByRole("button", { name: "Registrar pago" }).click();

  await expect(page.locator("tr", { hasText: numeroRecibo })).toBeVisible();
});

test("Dirección emite documentos generales y Pagos solo ve las constancias de solvencia", async ({ page }) => {
  await entrarComo(page, "dir.demo");
  await expect(page).toHaveURL(/\/administrativo$/);

  await menu(page).getByRole("link", { name: "Documentos" }).click();
  await expect(page.getByRole("heading", { name: "Documentos emitidos" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Emitir documento" })).toBeVisible();

  // El tipo "Constancia de solvencia" no debe ofrecerse acá — tiene su propio
  // camino en /solvency/.../certificate/ (RF-08), este endpoint la rechaza.
  await expect(page.locator("#document_type option", { hasText: "Constancia de solvencia" })).toHaveCount(0);

  await elegirEstudiante(page, "enrollment", "María Ximena");
  await page.getByLabel("Tipo de documento").selectOption({ label: "Constancia de estudio" });
  const descargaConstancia = page.waitForEvent("download");
  await page.getByRole("button", { name: "Emitir" }).click();
  await descargaConstancia;
  await expect(page.locator("tr", { hasText: "Constancia de estudio" }).first()).toBeVisible();

  // Carta membretada: único tipo con texto libre.
  await page.getByLabel("Tipo de documento").selectOption({ label: "Carta membretada" });
  await expect(page.getByLabel("Texto de la carta")).toBeVisible();
  await page.getByLabel("Texto de la carta").fill("A quien corresponda: constancia de buena conducta.");
  const descargaCarta = page.waitForEvent("download");
  await page.getByRole("button", { name: "Emitir" }).click();
  await descargaCarta;
  await expect(page.locator("tr", { hasText: "Carta membretada" }).first()).toBeVisible();

  await page.getByRole("button", { name: "Cerrar sesión" }).click();
  await entrarComo(page, "pagos.demo");
  await menu(page).getByRole("link", { name: "Documentos" }).click();

  // Pagos no emite documentos generales: el formulario no se muestra.
  await expect(page.getByRole("heading", { name: "Emitir documento" })).toHaveCount(0);
  // Su bandeja está limitada a constancias de solvencia (alcance del backend).
  await expect(page.locator("tr", { hasText: "Constancia de estudio" })).toHaveCount(0);
  await expect(page.locator("tr", { hasText: "Carta membretada" })).toHaveCount(0);
});

test("Dirección genera, aprueba y publica boletines, y RN-09 bloquea la publicación de un insolvente", async ({
  page,
}) => {
  await entrarComo(page, "dir.demo");
  await expect(page).toHaveURL(/\/administrativo$/);

  await menu(page).getByRole("link", { name: "Boletines" }).click();
  await expect(page.getByRole("heading", { name: "Boletines" })).toBeVisible();

  // Segundo básico: María Ximena (solvente) y Juan Carlos (becado) — ambos
  // publican sin problema para la Unidad 1 (el plazo de RN-10 ya pasó).
  await page.getByLabel("Sección").selectOption({ label: "Segundo básico" });
  await page.getByLabel("Unidad").selectOption({ label: "Unidad 1" });
  await page.getByRole("button", { name: "Generar boletines" }).click();

  const filaMaria = page.locator("tr", { hasText: "María Ximena" });
  await expect(filaMaria).toBeVisible();
  await expect(filaMaria.getByText("Borrador")).toBeVisible();

  await filaMaria.getByRole("button", { name: "Aprobar" }).click();
  // La siembra no tiene notas: aprobar avisa que el boletín sale con notas
  // pendientes y pide confirmarlo.
  await expect(page.getByRole("dialog")).toContainText("notas pendientes");
  await page.getByRole("dialog").getByRole("button", { name: "Aprobar igual" }).click();
  await expect(filaMaria.getByText("Aprobado")).toBeVisible();

  await filaMaria.getByRole("button", { name: "Publicar" }).click();
  await expect(filaMaria.getByText("Publicado")).toBeVisible();

  // Tercero básico: Ana Lucía no tiene ningún pago — RN-09 debe bloquear
  // la publicación con el mensaje real del backend, no uno inventado.
  await page.getByLabel("Sección").selectOption({ label: "Tercero básico" });
  await page.getByLabel("Unidad").selectOption({ label: "Unidad 1" });
  await page.getByRole("button", { name: "Generar boletines" }).click();

  const filaAna = page.locator("tr", { hasText: "Ana Lucía" });
  await expect(filaAna).toBeVisible();
  await filaAna.getByRole("button", { name: "Aprobar" }).click();
  // La siembra no tiene notas: aprobar avisa que el boletín sale con notas
  // pendientes y pide confirmarlo.
  await expect(page.getByRole("dialog")).toContainText("notas pendientes");
  await page.getByRole("dialog").getByRole("button", { name: "Aprobar igual" }).click();
  await expect(filaAna.getByText("Aprobado")).toBeVisible();

  await filaAna.getByRole("button", { name: "Publicar" }).click();
  await expect(page.getByText(/pagos pendientes/)).toBeVisible();
});
