import { expect, test, type APIRequestContext, type Page } from "@playwright/test";

import { elegirEnBuscador, menu } from "./utils";

/**
 * Fase 17 (RF-13 revisado, RN-18; RF-25/RF-37 revisados, RF-38, RN-19;
 * RF-39, RF-40, RN-20 a RN-22): el docente publica avisos y solo
 * administra los suyos, inicia una conversación con un encargado que la
 * familia responde (con "sin leer" por persona), reparte los puntos de una
 * unidad y la promedia, y la familia ve la nota promediada. Requiere
 * `manage.py seed_demo` (docente.demo da Matemática en "Segundo básico",
 * donde están María Ximena y Juan Carlos, vinculados a familia.demo).
 *
 * Usa la Unidad 2 a propósito: `notas` y `portal-publico` trabajan la
 * Unidad 1 (tope de 100 puntos y boletín publicado). Se puede correr
 * después de los demás specs, pero no dos veces sobre la misma base.
 */

const API = "http://localhost:8000/api/v1";
const CONTRASENA = "CambiaEstaClave2026";
const MATEMATICA = "Matemática — Segundo básico";

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

/** Al cargar la pantalla y al cambiar de curso se vuelven a pedir las
 * unidades y se elige la primera; se repite la elección hasta que se
 * mantenga, en lugar de adivinar cuándo terminó esa carga. */
async function elegirMatematicaUnidad2(page: Page): Promise<void> {
  const curso = page.getByLabel("Curso y sección");
  const unidad = page.getByLabel("Unidad");
  await expect(curso.locator("option", { hasText: MATEMATICA })).toHaveCount(1);
  await expect(async () => {
    await curso.selectOption({ label: MATEMATICA });
    await unidad.selectOption({ label: "Unidad 2" });
    await page.waitForTimeout(400);
    await expect(curso.locator("option:checked")).toHaveText(MATEMATICA);
    await expect(unidad.locator("option:checked")).toHaveText("Unidad 2");
  }).toPass();
}

async function salir(page: Page): Promise<void> {
  await page.getByRole("button", { name: "Cerrar sesión" }).first().click();
  await expect(page).toHaveURL(/\/ingresar/);
}

test("avisos: el docente publica y solo puede editar o retirar los suyos", async ({ page, request }) => {
  const authDir = { Authorization: `Bearer ${await tokenPara(request, "dir.demo")}` };
  await request.post(`${API}/announcements/`, {
    headers: authDir,
    data: { title: "Aviso de Dirección F17", content: "Para todos.", audience: "todos" },
  });

  await entrarComo(page, "docente.demo");
  await expect(page).toHaveURL(/\/operativo$/);
  await menu(page).getByRole("link", { name: "Avisos" }).click();
  await page.getByRole("button", { name: "Publicar aviso" }).click();
  await page.getByLabel("Título").fill("Aviso de la docente F17");
  await page.getByLabel("Contenido").fill("Traer cuaderno de matemática.");
  await page.getByLabel("Destinatario").selectOption({ label: "Una sección" });
  await page.getByLabel("Sección").selectOption({ label: "Segundo básico" });
  await page.getByRole("button", { name: "Publicar", exact: true }).click();

  const propio = page.locator("li", { hasText: "Aviso de la docente F17" });
  await expect(propio.getByRole("button", { name: "Editar" })).toBeVisible();
  const ajeno = page.locator("li", { hasText: "Aviso de Dirección F17" });
  await expect(ajeno).toBeVisible();
  await expect(ajeno.getByRole("button", { name: "Editar" })).toHaveCount(0);
  await expect(ajeno.getByRole("button", { name: "Retirar" })).toHaveCount(0);

  await propio.getByRole("button", { name: "Editar" }).click();
  await page.getByLabel("Título").fill("Aviso de la docente F17 (editado)");
  await page.getByRole("button", { name: "Guardar cambios" }).click();
  await expect(page.getByText("Aviso de la docente F17 (editado)")).toBeVisible();

  // RF-36: la familia de Segundo básico lo ve en su portal.
  await salir(page);
  await entrarComo(page, "familia.demo");
  await expect(page).toHaveURL(/\/portal$/);
  await page.getByRole("button", { name: "Avisos" }).click();
  await expect(page.getByText("Aviso de la docente F17 (editado)")).toBeVisible();
});

test("buzón: el docente inicia una conversación, la familia la lee y responde, y cada quien lleva su no leído", async ({
  page,
}) => {
  await entrarComo(page, "docente.demo");
  await menu(page).getByRole("link", { name: "Buzón" }).click();
  await page.getByRole("button", { name: "Nuevo mensaje" }).click();
  await elegirEnBuscador(page, "Para (encargado / alumno)", "María Ximena");
  await page.locator("#asunto-nuevo").fill("Tarea de matemática F17");
  await page.locator("#contenido-nuevo").fill("María Ximena no entregó la tarea del lunes.");
  await page.getByRole("button", { name: "Enviar", exact: true }).click();
  await expect(page.getByText("María Ximena no entregó la tarea del lunes.")).toBeVisible();
  await expect(page.getByText("Encargada Demo / María Ximena Pérez Tzul")).toBeVisible();

  await salir(page);
  await entrarComo(page, "familia.demo");
  await expect(page).toHaveURL(/\/portal$/);
  // RN-19: la pestaña del buzón avisa que hay algo sin leer.
  await expect(menu(page).getByText("sin leer")).toHaveCount(1);
  await page.getByRole("button", { name: "Avisos" }).click();
  const conversacion = page.getByRole("button", { name: /Tarea de matemática F17/ });
  await expect(conversacion).toContainText("Sin leer");
  await conversacion.click();
  await expect(page.getByText("María Ximena no entregó la tarea del lunes.")).toBeVisible();
  await page.getByLabel("Responder").fill("Gracias, mañana la entrega.");
  await page.getByRole("button", { name: "Enviar respuesta" }).click();
  await expect(page.getByText("Gracias, mañana la entrega.")).toBeVisible();
  await expect(menu(page).getByText("sin leer")).toHaveCount(0);

  await salir(page);
  await entrarComo(page, "docente.demo");
  // Ahora el que tiene algo sin leer es el docente.
  await expect(menu(page).getByRole("link", { name: /Buzón/ })).toContainText("sin leer");
  await menu(page).getByRole("link", { name: /Buzón/ }).click();
  const enBandeja = page.getByRole("button", { name: /Tarea de matemática F17/ });
  await expect(enBandeja).toContainText("Sin leer");
  await enBandeja.click();
  await expect(page.getByText("Gracias, mañana la entrega.")).toBeVisible();

  // El calendario sigue funcionando para el docente.
  await menu(page).getByRole("link", { name: "Calendario" }).click();
  await expect(page.getByRole("heading", { name: /Calendario/ })).toBeVisible();
});

test("notas: el docente reparte los puntos, promedia la unidad y la familia ve la nota promediada", async ({
  page,
  request,
}) => {
  await entrarComo(page, "docente.demo");
  await menu(page).getByRole("link", { name: "Diseñar unidad" }).click();
  await elegirMatematicaUnidad2(page);

  // RF-39: tres actividades sin punteo todavía.
  for (const nombre of ["Tarea F17", "Laboratorio F17", "Proyecto F17"]) {
    await page.getByRole("button", { name: "Agregar actividad" }).click();
    await page.getByLabel("Nombre de la actividad").fill(nombre);
    await page.getByLabel("Tipo").selectOption({ index: 1 });
    await page.getByLabel("Fecha de entrega").fill("2026-04-01");
    await page.getByRole("button", { name: "Guardar", exact: true }).click();
    await expect(page.locator("tr", { hasText: nombre })).toContainText("Sin punteo");
  }
  await page.getByRole("button", { name: "Repartir puntos" }).click();
  await page.getByRole("button", { name: "Repartir puntos" }).last().click();
  await expect(page.getByText("100 de 100 puntos usados")).toBeVisible();
  await expect(page.locator("tr", { hasText: "Proyecto F17" })).toContainText("33.34");

  // Se califican dos de las tres; el proyecto ya no se hará.
  const authDocente = { Authorization: `Bearer ${await tokenPara(request, "docente.demo")}` };
  const authDir = { Authorization: `Bearer ${await tokenPara(request, "dir.demo")}` };
  const estudiantes = (await (await request.get(`${API}/students/`, { headers: authDir })).json()).results;
  const maria = estudiantes.find((e: { internal_code: string }) => e.internal_code === "ES001");
  const inscripciones = (
    await (await request.get(`${API}/enrollments/`, { headers: authDir, params: { page_size: 200 } })).json()
  ).results;
  const inscripcionMaria = inscripciones.find(
    (i: { student: string; section_type: string }) => i.student === maria.public_id && i.section_type === "academica",
  );
  const actividades = (
    await (await request.get(`${API}/activities/`, { headers: authDocente, params: { page_size: 200 } })).json()
  ).results;
  for (const nombre of ["Tarea F17", "Laboratorio F17"]) {
    const actividad = actividades.find((a: { name: string }) => a.name === nombre);
    const respuesta = await request.post(`${API}/grades/`, {
      headers: authDocente,
      data: { enrollment: inscripcionMaria.public_id, activity: actividad.public_id, raw_score: "30" },
    });
    expect(respuesta.ok()).toBeTruthy();
  }

  // RF-40: promediar, dando de baja la actividad que no se hará.
  await page.reload();
  await elegirMatematicaUnidad2(page);
  await page.getByRole("button", { name: "Promediar unidad" }).click();
  await page.getByLabel(/Proyecto F17/).check();
  await page.getByRole("button", { name: "Promediar unidad" }).last().click();
  await expect(page.getByText("Promediada sobre 66.66 pts")).toBeVisible();
  await expect(page.locator("tr", { hasText: "Proyecto F17" })).toHaveCount(0);

  await menu(page).getByRole("link", { name: "Capturar notas" }).click();
  await elegirMatematicaUnidad2(page);
  await expect(page.getByText("Promediada sobre 66.66 pts")).toBeVisible();

  // 60 de 66.66 puntos evaluados = 90.01 sobre 100.
  await salir(page);
  await entrarComo(page, "familia.demo");
  await expect(page).toHaveURL(/\/portal$/);
  await page.getByRole("button", { name: "Cambiar estudiante" }).click();
  await page.getByRole("button", { name: /María Ximena Pérez Tzul/ }).click();
  await page.getByRole("button", { name: "Notas" }).click();
  await expect(page.getByText("Unidad 2 — 90.01 / 100")).toBeVisible();
});
