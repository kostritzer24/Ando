import { isAxiosError } from "axios";

import { http } from "@/app/http";
import { crearRecursoCrud } from "@/shared/api/resource";
import type { Activity, ActivityType, Grade, GradeChangeRequest, GradingUnit } from "@/shared/types/models";

export const activitiesApi = crearRecursoCrud<Activity>("/activities/");
export const activityTypesApi = crearRecursoCrud<ActivityType>("/activity-types/");
export const gradesApi = crearRecursoCrud<Grade>("/grades/");
export const gradeChangeRequestsApi = crearRecursoCrud<GradeChangeRequest>("/grade-change-requests/");

export function unidadesDeCiclo(cyclePublicId: string) {
  return crearRecursoCrud<GradingUnit>(`/cycles/${cyclePublicId}/units/`);
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
): Promise<GradeChangeRequest> {
  const ruta = aprobar ? "approve" : "reject";
  const { data } = await http.post<GradeChangeRequest>(`/grade-change-requests/${publicId}/${ruta}/`);
  return data;
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
  resumen: { crear: number; modificacion: number; sin_cambio: number };
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
