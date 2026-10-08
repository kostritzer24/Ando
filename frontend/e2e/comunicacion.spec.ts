import { expect, test, type APIRequestContext, type Page } from "@playwright/test";

import { menu } from "./utils";

/**
 * Fase 11 (RF-13, RF-24, RF-25, RF-35 a RF-37, RN-16): avisos de
 * cartelera con destinatario, reportes de conducta con descarga de PDF,
 * y buzón con filtro de lenguaje inapropiado y bloqueo temporal — en los
 * tres portales (administrativo/operativo para Dirección y el maestro
 * guía, portal público para la familia). Requiere `manage.py seed_demo`
 * (guia.demo es maestro guía de "Primero básico A", donde está inscrito
 * Diego Alejandro Ramírez Cabrera; docente.demo da Matemática en
 * "Segundo básico").
 *
 * El aviso, el vínculo de Diego con familia.demo y el mensaje inicial del
 * buzón se arman por API directa — lo nuevo de esta fase es cómo cada
 * pantalla muestra y usa esos datos, no los flujos de inscripción/vínculo
 * ya probados en la Fase 5.
 */

const API = "http://localhost:8000/api/v1";
const CONTRASENA = "CambiaEstaClave2026";

async function tokenPara(request: APIRequestContext, usuario: string): Promise<string> {
  const respuesta = await request.post(`${API}/auth/login/`, {
    data: { username: usuario, password: CONTRASENA },
  });
  return (await respuesta.json()).access;
}

async function entrarComo(page: Page, usuario: string): Promise<void> {
  await page.goto("/ingresar");
  await page.getByLabel("Usuario").fill(usuario);
  await page.getByLabel("Contraseña").fill(CONTRASENA);
  await page.getByRole("button", { name: "Entrar" }).click();
}

test("avisos: Dirección publica para todos y por sección, y cada rol ve solo lo que le corresponde", async ({
  page,
  request,
}) => {
  const tokenDir = await tokenPara(request, "dir.demo");
  const authDir = { Authorization: `Bearer ${tokenDir}` };

  const secciones = (await (await request.get(`${API}/sections/`, { headers: authDir })).json()).results;
  const segundoBasico = secciones.find((s: { grade: string; letter: string }) => s.grade === "Segundo básico");
  const primeroA = secciones.find(
    (s: { grade: string; letter: string }) => s.grade === "Primero básico" && s.letter === "A",
  );

  await request.post(`${API}/announcements/`, {
    headers: authDir,
    data: { title: "Suspensión de labores", content: "Por lluvia.", audience: "todos" },
  });
  await request.post(`${API}/announcements/`, {
    headers: authDir,
    data: {
      title: "Reunión Segundo básico",
      content: "Jueves 8am.",
      audience: "seccion",
      target_section: segundoBasico.public_id,
    },
  });
  await request.post(`${API}/announcements/`, {
    headers: authDir,
    data: {
      title: "Reunión Primero básico A",
      content: "Viernes 8am.",
      audience: "seccion",
      target_section: primeroA.public_id,
    },
  });

  await entrarComo(page, "docente.demo");
  await expect(page).toHaveURL(/\/operativo$/);
  await menu(page).getByRole("link", { name: "Avisos" }).click();
  await expect(page.getByRole("heading", { name: "Cartelera de avisos" })).toBeVisible();
  await expect(page.getByText("Suspensión de labores")).toBeVisible();
  await expect(page.getByText("Reunión Segundo básico")).toBeVisible();
  await expect(page.getByText("Reunión Primero básico A")).toHaveCount(0);
});

test("reportes de conducta: el maestro guía registra uno con artículos marcados y descarga el PDF", async ({
  page,
  request,
}) => {
  const tokenDir = await tokenPara(request, "dir.demo");
  const authDir = { Authorization: `Bearer ${tokenDir}` };
  const articulos = (
    await (await request.get(`${API}/conduct-rule-articles/`, { headers: authDir })).json()
  ).results;
  const primerArticulo = articulos[0];

  await entrarComo(page, "guia.demo");
  await expect(page).toHaveURL(/\/operativo$/);
  await menu(page).getByRole("link", { name: "Reportes de conducta" }).click();
  await expect(page.getByRole("heading", { name: "Reportes de conducta" })).toBeVisible();

  await page.getByRole("button", { name: "Registrar reporte" }).click();
  await page.getByLabel("Fecha").fill("2026-03-10");
  await page.getByLabel("Hechos ocurridos").fill("Se retiró del aula sin permiso.");
  await page.getByLabel("Medidas inmediatas tomadas").fill("Se conversó con el estudiante.");
  await page.getByText(`${primerArticulo.code} — ${primerArticulo.description}`).click();
  await page.getByLabel("Compromisos establecidos").fill("Pedir permiso antes de salir.");
  await page.getByRole("button", { name: "Guardar reporte" }).click();

  await expect(page.getByRole("heading", { name: "Registrar reporte de conducta" })).not.toBeVisible();
  const fila = page.locator("tr", { hasText: "10/03/2026" });
  await expect(fila).toBeVisible();

  const descarga = page.waitForEvent("download");
  await fila.getByRole("button", { name: "Descargar PDF" }).click();
  await descarga;
});

test("buzón y RN-16: la familia escribe, el maestro guía responde, y el lenguaje inapropiado se rechaza", async ({
  page,
  request,
}) => {
  const tokenDir = await tokenPara(request, "dir.demo");
  const authDir = { Authorization: `Bearer ${tokenDir}` };

  const estudiantes = (await (await request.get(`${API}/students/`, { headers: authDir })).json()).results;
  const diego = estudiantes.find((e: { internal_code: string }) => e.internal_code === "ES004");
  const guardianes = (await (await request.get(`${API}/guardians/`, { headers: authDir })).json()).results;
  const encargadaDemo = guardianes.find((g: { full_name: string }) => g.full_name === "Encargada Demo");
  await request.post(`${API}/guardians/${encargadaDemo.public_id}/link-student/`, {
    headers: authDir,
    data: { student: diego.public_id, relationship: "Madre" },
  });

  const tokenFamilia = await tokenPara(request, "familia.demo");
  const authFamilia = { Authorization: `Bearer ${tokenFamilia}` };
  const inscripciones = (
    await (await request.get(`${API}/enrollments/`, { headers: authFamilia })).json()
  ).results;
  const inscripcionDiego = inscripciones.find((i: { student: string }) => i.student === diego.public_id);

  await request.post(`${API}/messages/`, {
    headers: authFamilia,
    data: { section: inscripcionDiego.section, subject: "Consulta", content: "¿Hay actividad el viernes?" },
  });

  await entrarComo(page, "guia.demo");
  await expect(page).toHaveURL(/\/operativo$/);
  await menu(page).getByRole("link", { name: "Buzón" }).click();
  await expect(page.getByRole("heading", { name: "Buzón" })).toBeVisible();
  await page.getByRole("button", { name: /Consulta/ }).click();
  await page.getByLabel("Responder").fill("Sí, hay una actividad especial.");
  await page.getByRole("button", { name: "Enviar respuesta" }).click();
  await expect(page.getByText("Respondido")).toBeVisible();

  await page.getByRole("button", { name: "Cerrar sesión" }).click();
  await entrarComo(page, "familia.demo");
  await expect(page).toHaveURL(/\/portal$/);

  await page.getByRole("button", { name: "Cambiar estudiante" }).click();
  await page.getByRole("button", { name: /Diego Alejandro Ramírez Cabrera/ }).click();

  // RF-35: el reporte de conducta que registró guia.demo en la prueba
  // anterior ya debería verse en el portal de la familia.
  await page.getByRole("button", { name: "Asistencia" }).click();
  await expect(page.getByText("Se retiró del aula sin permiso.")).toBeVisible();

  await page.getByRole("button", { name: "Avisos" }).click();
  await expect(page.getByRole("heading", { name: "Avisos" })).toBeVisible();
  await expect(page.getByText("Sí, hay una actividad especial.")).toBeVisible();

  await page.locator("#subject").fill("Otra consulta");
  await page.locator("#content").fill("El maestro es un idiota");
  await page.getByRole("button", { name: "Enviar" }).click();
  await expect(page.getByText(/lenguaje inapropiado/)).toBeVisible();
});
