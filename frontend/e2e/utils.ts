import type { Page } from "@playwright/test";

/** La navegación principal del portal. Los clics del menú se acotan acá
 * porque la página de Inicio también enlaza a varias de esas pantallas,
 * y `getByRole("link", { name })` busca por subcadena. */
export function menu(page: Page) {
  return page.getByRole("navigation", { name: "Navegación principal" });
}

/** Elige una opción de un selector con búsqueda (FormBuscador): escribe parte
 * del texto y hace clic en la primera coincidencia de la lista. */
export async function elegirEnBuscador(page: Page, etiqueta: string, texto: string): Promise<void> {
  const campo = page.getByLabel(etiqueta, { exact: true });
  await campo.click();
  await campo.fill(texto);
  await page.getByRole("option", { name: texto }).first().click();
}

/** Igual, pero la primera opción de la lista sin escribir nada. */
export async function elegirPrimeraDelBuscador(page: Page, etiqueta: string): Promise<void> {
  const campo = page.getByLabel(etiqueta, { exact: true });
  await campo.click();
  await page.getByRole("option").first().click();
}
