import { expect, test, type APIRequestContext, type Page } from "@playwright/test";

/**
 * Fase 10 (RF-27 a RF-29, RF-31 a RF-34): portal público de familias —
 * selector de estudiante (HU-27), calendario semanal de entrada
 * (RF-28/RF-32), notas por curso y unidad con descarga de boletín
 * (RF-29/RF-34), asistencia (RF-31), solvencia y descarga de constancia
 * (RF-33) — más la página pública de verificación por QR (RF-14,
 * pendiente de la Fase 9). Requiere `manage.py seed_demo` (María Ximena
 * y Juan Carlos vinculados a familia.demo, docente.demo asignado a
 * Matemática/Segundo básico).
 *
 * El horario, el calendario, la nota y la asistencia de esta prueba se
 * arman por API directa (como Dirección) en vez de repetir los flujos de
 * las Fases 6 a 9, que ya se prueban en sus propios specs — acá lo nuevo
 * es cómo el portal público las muestra.
 */

const API = "http://localhost:8000/api/v1";
const CONTRASENA = "CambiaEstaClave2026";

async function tokenPara(request: APIRequestContext, usuario: string): Promise<string> {
  const respuesta = await request.post(`${API}/auth/login/`, {
    data: { username: usuario, password: CONTRASENA },
  });
  const cuerpo = await respuesta.json();
  return cuerpo.access;
}

async function entrarComo(page: Page, usuario: string): Promise<void> {
  await page.goto("/ingresar");
  await page.getByLabel("Usuario").fill(usuario);
  await page.getByLabel("Contraseña").fill(CONTRASENA);
  await page.getByRole("button", { name: "Entrar" }).click();
}

function lunesDeEstaSemana(): string {
  const hoy = new Date();
  const offset = hoy.getDay() === 0 ? -6 : 1 - hoy.getDay();
  const lunes = new Date(hoy);
  lunes.setDate(hoy.getDate() + offset);
  return lunes.toISOString().slice(0, 10);
}

test("familia consulta el calendario, las notas, la asistencia y la solvencia de su hija, y verifica su constancia por QR", async ({
  page,
  request,
}) => {
  const token = await tokenPara(request, "dir.demo");
  const auth = { Authorization: `Bearer ${token}` };

  const estudiantes = (await (await request.get(`${API}/students/`, { headers: auth })).json()).results;
  const maria = estudiantes.find((e: { internal_code: string }) => e.internal_code === "ES001");

  const secciones = (await (await request.get(`${API}/sections/`, { headers: auth })).json()).results;
  const segundoBasico = secciones.find((s: { grade: string }) => s.grade === "Segundo básico");

  const ciclos = (await (await request.get(`${API}/cycles/`, { headers: auth })).json()).results;
  const ciclo = ciclos[0];
  const unidades = (await (await request.get(`${API}/cycles/${ciclo.public_id}/units/`, { headers: auth })).json())
    .results;
  const unidad1 = unidades.find((u: { number: number }) => u.number === 1);

  const asignaciones = (await (await request.get(`${API}/assignments/`, { headers: auth })).json()).results;
  const asignacionMatematica = asignaciones.find(
    (a: { section: string; course_name: string }) =>
      a.section === segundoBasico.public_id && a.course_name === "Matemática",
  );

  const inscripciones = (await (await request.get(`${API}/enrollments/`, { headers: auth })).json()).results;
  const inscripcionMaria = inscripciones.find(
    (i: { student: string; section: string }) => i.student === maria.public_id && i.section === segundoBasico.public_id,
  );

  // Horario: Matemática el lunes, período 1.
  await request.post(`${API}/schedule-blocks/`, {
    headers: auth,
    data: { assignment: asignacionMatematica.public_id, day_of_week: "lunes", period_number: 1 },
  });

  // Calendario: aviso institucional el lunes de esta semana.
  await request.post(`${API}/calendar-events/`, {
    headers: auth,
    data: {
      title: "Reunión de padres",
      type: "institucional",
      event_date: lunesDeEstaSemana(),
      start_time: "07:00",
      end_time: "07:30",
    },
  });

  // Nota: una actividad de Matemática, Unidad 1, calificada.
  const tiposActividad = (await (await request.get(`${API}/activity-types/`, { headers: auth })).json()).results;
  const actividad = await (
    await request.post(`${API}/activities/`, {
      headers: auth,
      data: {
        assignment: asignacionMatematica.public_id,
        unit: unidad1.public_id,
        activity_type: tiposActividad[0].public_id,
        name: "Examen de unidad",
        max_score: "100",
        due_date: unidad1.end_date,
      },
    })
  ).json();
  await request.post(`${API}/grades/`, {
    headers: auth,
    data: { enrollment: inscripcionMaria.public_id, activity: actividad.public_id, raw_score: "85" },
  });

  // Asistencia: presente hoy.
  await request.post(`${API}/attendance/`, {
    headers: auth,
    data: {
      enrollment: inscripcionMaria.public_id,
      date: new Date().toISOString().slice(0, 10),
      status: "presente",
    },
  });

  // Solvencia: María ya está al día por la siembra — solo hace falta
  // emitir la constancia para que el portal tenga algo que descargar.
  await request.post(`${API}/solvency/${inscripcionMaria.public_id}/certificate/`, { headers: auth });
  const documentos = (await (await request.get(`${API}/documents/`, { headers: auth })).json()).results;
  const constancia = documentos.find((d: { enrollment: string }) => d.enrollment === inscripcionMaria.public_id);

  // Boletín: generar, aprobar y publicar la Unidad 1 de Segundo básico.
  const generados = await (
    await request.post(`${API}/report-cards/generate/`, {
      headers: auth,
      data: { section: segundoBasico.public_id, unit: unidad1.public_id },
    })
  ).json();
  const boletinMaria = generados.find((b: { enrollment: string }) => b.enrollment === inscripcionMaria.public_id);
  await request.post(`${API}/report-cards/${boletinMaria.public_id}/approve/`, { headers: auth });
  await request.post(`${API}/report-cards/${boletinMaria.public_id}/publish/`, { headers: auth });

  // --- Portal público, ya con datos reales que consultar. ---
  await entrarComo(page, "familia.demo");
  await expect(page).toHaveURL(/\/portal$/);

  // "López Xitumul" ordena antes que "Pérez Tzul" (Student.Meta.ordering
  // es por apellido) — Juan Carlos queda elegido por omisión, así que
  // hay que elegir a María explícitamente antes de seguir.
  await page.getByRole("button", { name: "Cambiar estudiante" }).click();
  await page.getByRole("button", { name: /María Ximena Pérez Tzul/ }).click();

  await expect(page.getByRole("heading", { name: "Calendario de la semana" })).toBeVisible();
  await page.getByRole("button", { name: /^lun/ }).click();
  const filaMatematica = page.locator("li", { hasText: "Matemática" });
  await expect(filaMatematica).toBeVisible();
  const filaAviso = page.locator("li", { hasText: "Reunión de padres" });
  await expect(filaAviso).toBeVisible();
  await expect(filaAviso.getByText("Aviso", { exact: true })).toBeVisible();

  await page.getByRole("button", { name: "Notas" }).click();
  await expect(page.getByRole("heading", { name: "Notas" })).toBeVisible();
  await expect(page.getByText("Matemática")).toBeVisible();
  await expect(page.getByText("Unidad 1 — 85 / 100")).toBeVisible();
  const descargaBoletin = page.waitForEvent("download");
  await page.getByRole("button", { name: "Descargar" }).click();
  await descargaBoletin;

  await page.getByRole("button", { name: "Asistencia" }).click();
  await expect(page.getByRole("heading", { name: "Asistencia" })).toBeVisible();
  await expect(page.getByText("Jornada matutina")).toBeVisible();
  await expect(page.getByText("Presente")).toBeVisible();

  await page.getByRole("button", { name: "Pagos" }).click();
  await expect(page.getByText("Al día con los pagos.")).toBeVisible();
  const descargaConstancia = page.waitForEvent("download");
  await page.getByRole("button", { name: "Descargar" }).click();
  await descargaConstancia;

  // HU-27: cambiar de estudiante sin volver a iniciar sesión.
  await page.getByRole("button", { name: "Cambiar estudiante" }).click();
  await expect(page.getByRole("heading", { name: "Cambiar estudiante" })).toBeVisible();
  await page.getByRole("button", { name: /Juan Carlos López Xitumul/ }).click();
  await expect(page.locator(".top-app-bar__nombre-texto")).toHaveText("Juan Carlos López Xitumul");
  await expect(page.getByText("Solvente por beca.")).toBeVisible();

  // RF-14: la constancia de María se verifica por su código QR, sin sesión.
  await page.getByRole("button", { name: "Cerrar sesión" }).click();
  await page.goto(`/verificar/${constancia.verification_code}`);
  await expect(page.getByText("Documento válido")).toBeVisible();
  await expect(page.getByText("María Ximena Pérez Tzul")).toBeVisible();

  await page.goto("/verificar/codigo-que-no-existe");
  await expect(page.getByText("Este código no corresponde a un documento válido.")).toBeVisible();
});
