import { isAxiosError } from "axios";

import { http } from "@/app/http";
import { crearRecursoCrud } from "@/shared/api/resource";
import type {
  Activity,
  ActivityType,
  EstadoDeUnidad,
  Grade,
  GradeChangeRequest,
  GradingUnit,
  NotaDeUnidad,
} from "@/shared/types/models";

export const activitiesApi = crearRecursoCrud<Activity>("/activities/");
export const activityTypesApi = crearRecursoCrud<ActivityType>("/activity-types/");
export const gradesApi = crearRecursoCrud<Grade>("/grades/");
export const gradeChangeRequestsApi = crearRecursoCrud<GradeChangeRequest>("/grade-change-requests/");

export function unidadesDeCiclo(cyclePublicId: string) {
  return crearRecursoCrud<GradingUnit>(`/cycles/${cyclePublicId}/units/`);
}

/** RF-39: reparte los 100 puntos entre las actividades sin notas. */
export async function repartirPuntos(assignment: string, unit: string): Promise<Activity[]> {
  const { data } = await http.post<Activity[]>("/activities/distribute/", { assignment, unit });
  return data;
}

/** RF-40: si la unidad está promediada, sobre cuántos puntos, y si ya no
 * se puede cambiar (hay un boletín aprobado). */
export async function estadoDeUnidad(assignment: string, unit: string): Promise<EstadoDeUnidad> {
  const { data } = await http.get<EstadoDeUnidad>("/activities/unit-status/", {
    params: { assignment, unit },
  });
  return data;
}

export async function cambiarPromedio(payload: {
  assignment: string;
  unit: string;
  averaged: boolean;
  deactivate?: string[];
}): Promise<EstadoDeUnidad> {
  const { data } = await http.post<EstadoDeUnidad>("/activities/average/", payload);
  return data;
}

/** RF-29 / RN-22: nota de cada curso y unidad calculada en el servidor,
 * promediada o no — el portal no vuelve a sumar en el navegador. */
export async function notasDeUnidad(enrollment: string): Promise<NotaDeUnidad[]> {
  const { data } = await http.get<NotaDeUnidad[]>("/grades/unit-summary/", { params: { enrollment } });
  return data;
}

/** "Promediada sobre 70 pts" — la misma etiqueta en diseñar y en capturar. */
export function etiquetaPromedio(estado: EstadoDeUnidad | null): string {
  if (!estado?.promediada) return "";
  return `Promediada sobre ${Number(estado.puntos_evaluados)} pts`;
}

export async function registrarPunteo(payload: {
  enrollment: string;
  activity: string;
  raw_score: string;
}): Promise<Grade> {
  const { data } = await http.post<Grade>("/grades/", payload);
  return data;
}

export async function solicitarModificacion(payload: {
  grade: string;
  requested_score: string;
  reason: string;
}): Promise<GradeChangeRequest> {
  const { data } = await http.post<GradeChangeRequest>("/grade-change-requests/", payload);
  return data;
}

export async function resolverModificacion(
  publicId: string,
  aprobar: boolean,
  motivo = "",
): Promise<GradeChangeRequest> {
  const ruta = aprobar ? "approve" : "reject";
  const { data } = await http.post<GradeChangeRequest>(`/grade-change-requests/${publicId}/${ruta}/`, {
    motivo,
  });
  return data;
}

/** RN-05 dentro del plazo de entrega de la unidad: corrige la nota sin
 * pasar por Dirección (después del plazo, el backend responde 400 y hay
 * que pedir una corrección). */
export async function corregirNota(publicId: string, score: string): Promise<Grade> {
  const { data } = await http.post<Grade>(`/grades/${publicId}/correct/`, { score });
  return data;
}

/** Hasta el día de entrega de notas inclusive (mismo corte que el backend,
 * `puede_corregirse_sin_autorizacion`). */
export function enPlazoDeEntrega(unidad: GradingUnit | undefined, hoy = new Date()): boolean {
  if (!unidad?.grades_due_date) return false;
  const hoyIso = `${hoy.getFullYear()}-${String(hoy.getMonth() + 1).padStart(2, "0")}-${String(hoy.getDate()).padStart(2, "0")}`;
  return hoyIso <= unidad.grades_due_date;
}

/** El motivo que da el backend en un 400 ("ya hay una solicitud pendiente",
 * "debe estar entre 0 y 10"), que le dice a la persona qué corregir; si no
 * viene uno legible, `porOmision`. DRF lo manda como lista plana, como
 * `{campo: [mensaje]}` o como `{detail}`. */
export function motivoDelRechazo(error: unknown, porOmision: string): string {
  if (!isAxiosError(error) || error.response?.status !== 400) return porOmision;
  let cuerpo: unknown = error.response.data;
  while (cuerpo && typeof cuerpo === "object") {
    cuerpo = Array.isArray(cuerpo) ? cuerpo[0] : Object.values(cuerpo)[0];
  }
  return typeof cuerpo === "string" && cuerpo ? cuerpo : porOmision;
}

function nombreDeArchivo(headers: Record<string, unknown>, porOmision: string): string {
  const disposicion = String(headers["content-disposition"] ?? "");
  const coincidencia = /filename="?([^"]+)"?/.exec(disposicion);
  return coincidencia?.[1] ?? porOmision;
}

export async function descargarPlantillaNotas(
  assignmentPublicId: string,
  unitPublicId: string,
): Promise<{ blob: Blob; nombreArchivo: string }> {
  const respuesta = await http.get(`/grades/template/${assignmentPublicId}/${unitPublicId}/`, {
    responseType: "blob",
  });
  return {
    blob: respuesta.data as Blob,
    nombreArchivo: nombreDeArchivo(respuesta.headers, "plantilla_notas.xlsx"),
  };
}

export interface ResumenVistaPrevia {
  filas: number;
  resumen: { crear: number; correccion?: number; modificacion: number; sin_cambio: number };
  errores?: string[];
}

const RESUMEN_VACIO = { crear: 0, modificacion: 0, sin_cambio: 0 };

function normalizarError400(error: unknown): ResumenVistaPrevia {
  // Mismo par de formas que en la plantilla de asistencia (Fase 6): un
  // `raise ValidationError("...")` da una lista plana, la validación
  // fila por fila da {errores: [...]}.
  if (isAxiosError(error) && error.response?.status === 400) {
    const cuerpo = error.response.data as { errores?: string[] } | string[];
    if (Array.isArray(cuerpo)) {
      return { filas: 0, resumen: RESUMEN_VACIO, errores: cuerpo };
    }
    return { filas: 0, resumen: RESUMEN_VACIO, ...cuerpo };
  }
  throw error;
}

export async function previsualizarPlantillaNotas(payload: {
  assignment: string;
  unit: string;
  file: File;
}): Promise<ResumenVistaPrevia> {
  const formData = new FormData();
  formData.append("assignment", payload.assignment);
  formData.append("unit", payload.unit);
  formData.append("file", payload.file);
  try {
    const { data } = await http.post<ResumenVistaPrevia>("/grades/template/preview/", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data;
  } catch (error) {
    return normalizarError400(error);
  }
}

export interface ResultadoSubidaNotas {
  creados?: number;
  correcciones?: number;
  solicitudes_de_modificacion?: number;
  errores?: string[];
}

export async function subirPlantillaNotas(payload: {
  assignment: string;
  unit: string;
  file: File;
}): Promise<ResultadoSubidaNotas> {
  const formData = new FormData();
  formData.append("assignment", payload.assignment);
  formData.append("unit", payload.unit);
  formData.append("file", payload.file);
  try {
    const { data } = await http.post<ResultadoSubidaNotas>("/grades/template/upload/", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data;
  } catch (error) {
    if (isAxiosError(error) && error.response?.status === 400) {
      const cuerpo = error.response.data as { errores?: string[] } | string[];
      return Array.isArray(cuerpo) ? { errores: cuerpo } : cuerpo;
    }
    throw error;
  }
}
