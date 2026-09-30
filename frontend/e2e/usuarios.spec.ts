import { expect, test, type Page } from "@playwright/test";

import { menu } from "./utils";

/**
 * Administración de usuarios (RF-01) y permisos por área en el menú
 * (RNF-03). Requiere el backend local con `manage.py seed_demo`.
 * Hace 5 inicios de sesión: queda bajo el límite de 10 por minuto (RNF-05).
 */
async function entrarComo(page: Page, usuario: string, contrasena = "CambiaEstaClave2026"): Promise<void> {
  await page.goto("/ingresar");
  await page.getByLabel("Usuario").fill(usuario);
  await page.getByLabel("Contraseña").fill(contrasena);
  await page.getByRole("button", { name: "Entrar" }).click();
}

async function salir(page: Page): Promise<void> {
  await page.getByRole("button", { name: "Cerrar sesión" }).click();
  await expect(page).toHaveURL(/\/ingresar$/);
}

test("RF-01: el administrador crea una cuenta, la persona cambia su contraseña al entrar y una cuenta desactivada ya no entra", async ({
  page,
}) => {
  const nombreUsuario = `prueba.${Date.now()}`;

  await entrarComo(page, "admin.demo");
  await expect(page).toHaveURL(/\/administrativo$/);
  await menu(page).getByRole("link", { name: "Usuarios" }).click();
  await expect(page.getByRole("heading", { name: "Usuarios", level: 1 })).toBeVisible();

  await page.getByRole("button", { name: "Crear usuario" }).click();
  const dialogo = page.getByRole("dialog");
  await dialogo.getByLabel("Nombre de usuario").fill(nombreUsuario);
  await dialogo.getByLabel("Nombres").fill("Ana");
  await dialogo.getByLabel("Apellidos").fill("Prueba");
  await dialogo.getByLabel("Rol").selectOption({ label: "Docente" });
  await dialogo.getByRole("button", { name: "Crear usuario" }).click();

  await expect(dialogo.getByText("La cuenta quedó creada")).toBeVisible();
  const contrasena = (await dialogo.locator("dd").nth(1).textContent())?.trim() ?? "";
  expect(contrasena).toMatch(/^[A-Z][a-z]+-[A-Z][a-z]+-\d{4}$/);
  await dialogo.getByRole("button", { name: "Listo" }).click();
  await salir(page);

  // Primer ingreso: el sistema obliga a cambiar la contraseña temporal.
  await entrarComo(page, nombreUsuario, contrasena);
  await expect(page).toHaveURL(/\/cambiar-contrasena$/);
  await page.goto("/ingresar");

  await entrarComo(page, "admin.demo");
  await expect(page).toHaveURL(/\/administrativo$/);
  await page.goto("/administrativo/usuarios");
  await page.getByPlaceholder("Buscar por nombre o usuario").fill(nombreUsuario);
  await page.getByRole("button", { name: "Desactivar" }).click();
  await page.getByRole("dialog").getByRole("button", { name: "Desactivar" }).click();
  await expect(page.getByText("Cuenta desactivada.")).toBeVisible();
  await salir(page);

  await entrarComo(page, nombreUsuario, contrasena);
  await expect(page.getByRole("alert")).toContainText("Usuario o contraseña incorrectos");
});

test("RNF-03: el menú sale de la matriz del rol — el administrador ve Asistencia en consulta, pero no Buzón", async ({
  page,
}) => {
  await entrarComo(page, "admin.demo");
  await expect(page).toHaveURL(/\/administrativo$/);

  await expect(menu(page).getByRole("link", { name: "Bitácora" })).toBeVisible();
  await expect(menu(page).getByRole("link", { name: "Buzón" })).toHaveCount(0);
  await expect(menu(page).getByRole("link", { name: "Modificaciones de notas" })).toHaveCount(0);

  await menu(page).getByRole("link", { name: "Asistencia", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Asistencia", level: 1 })).toBeVisible();
  await expect(page.getByText("Consulta de la asistencia registrada")).toBeVisible();

  // Un enlace directo a una pantalla fuera de su matriz vuelve al inicio.
  await page.goto("/administrativo/buzon");
  await expect(page).toHaveURL(/\/administrativo$/);
});
