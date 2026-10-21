import { expect, test } from "@playwright/test";

// Requiere el usuario `cambio.demo` con contraseña temporal Lluviasolpino79
// y must_change_password=true (se prepara con manage.py shell).
test("primer ingreso: se elige la contraseña nueva sin volver a pedir la temporal", async ({
  page,
}) => {
  await page.goto("/ingresar");
  await page.getByLabel("Usuario").fill("cambio.demo");
  await page.getByLabel("Contraseña").fill("Lluviasolpino79");
  await page.getByRole("button", { name: /Ingresar|Entrar/ }).click();
  await expect(page).toHaveURL(/cambiar-contrasena/);
  await expect(page.getByLabel("Contraseña temporal")).toHaveCount(0);

  await page.getByLabel("Contraseña nueva", { exact: true }).pressSequentially("Teamosafi123");
  await page.getByLabel("Repite la contraseña nueva").pressSequentially("Otra-distinta-123");
  await page.getByRole("button", { name: "Guardar" }).click();
  await expect(page.getByText("Las dos contraseñas no coinciden")).toBeVisible();

  await page.getByLabel("Repite la contraseña nueva").fill("Teamosafi123");
  await page.getByRole("button", { name: "Guardar" }).click();
  await expect(page).not.toHaveURL(/cambiar-contrasena/);
});
