import type { Page } from "@playwright/test";

/** La navegación principal del portal. Los clics del menú se acotan acá
 * porque la página de Inicio también enlaza a varias de esas pantallas,
 * y `getByRole("link", { name })` busca por subcadena. */
export function menu(page: Page) {
  return page.getByRole("navigation", { name: "Navegación principal" });
}
