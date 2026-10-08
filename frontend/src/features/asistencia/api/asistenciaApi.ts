import { isAxiosError } from "axios";

import { http } from "@/app/http";
import { crearRecursoCrud } from "@/shared/api/resource";
import type { Attendance, Justification } from "@/shared/types/models";

export const attendanceApi = crearRecursoCrud<Attendance>("/attendance/");
export const justificationsApi = crearRecursoCrud<Justification>("/justifications/");

export async function registrarAsistencia(payload: {
  enrollment: string;
  date: string;
  status: string;
}): Promise<Attendance> {
  const { data } = await http.post<Attendance>("/attendance/", payload);
  return data;
}

export async function crearJustificacion(payload: {
  attendance: string;
  justification_type: string;
  reason_detail?: string;
  supporting_document?: File;
}): Promise<Justification> {
  const formData = new FormData();
  formData.append("attendance", payload.attendance);
  formData.append("justification_type", payload.justification_type);
  if (payload.reason_detail) formData.append("reason_detail", payload.reason_detail);
  if (payload.supporting_document) {
    formData.append("supporting_document", payload.supporting_document);
  }
  const { data } = await http.post<Justification>("/justifications/", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function resolverJustificacion(
  justificationPublicId: string,
  aprobar: boolean,
): Promise<Justification> {
  const { data } = await http.post<Justification>(
    `/justifications/${justificationPublicId}/resolve/`,
    { aprobar },
  );
  return data;
}

export async function descargarDocumentoJustificacion(
  justificationPublicId: string,
): Promise<{ blob: Blob; nombreArchivo: string }> {
  const respuesta = await http.get(`/justifications/${justificationPublicId}/document/`, {
    responseType: "blob",
  });
  const disposicion = String(respuesta.headers["content-disposition"] ?? "");
  const coincidencia = /filename="?([^"]+)"?/.exec(disposicion);
  return { blob: respuesta.data as Blob, nombreArchivo: coincidencia?.[1] ?? "documento" };
}

export async function descargarPlantillaAsistencia(
  sectionPublicId: string,
  fecha: string,
): Promise<{ blob: Blob; nombreArchivo: string }> {
  const respuesta = await http.get(`/attendance/template/${sectionPublicId}/${fecha}/`, {
    responseType: "blob",
  });
  const disposicion = String(respuesta.headers["content-disposition"] ?? "");
  const coincidencia = /filename="?([^"]+)"?/.exec(disposicion);
  return { blob: respuesta.data as Blob, nombreArchivo: coincidencia?.[1] ?? "plantilla.xlsx" };
}

export interface ResultadoPlantilla {
  creados?: number;
  errores?: string[];
}

export async function subirPlantillaAsistencia(payload: {
  section: string;
  date: string;
  file: File;
}): Promise<ResultadoPlantilla> {
  const formData = new FormData();
  formData.append("section", payload.section);
  formData.append("date", payload.date);
  formData.append("file", payload.file);
  try {
    const { data } = await http.post<ResultadoPlantilla>("/attendance/template/upload/", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data;
  } catch (error) {
    // El backend responde 400 de dos formas distintas para esta ruta:
    // {errores: [...]} cuando el archivo se pudo leer pero hay filas
    // que no cuadran (sección 14.4, no guarda nada), o una lista plana
    // ["mensaje"] cuando `raise ValidationError(...)` corta antes de
    // eso (extensión equivocada, sección que no es de taller, archivo
    // ilegible) — ninguna de las dos es un error de red, así que las
    // dos se muestran igual en la pantalla, no un error genérico.
    if (isAxiosError(error) && error.response?.status === 400) {
      const cuerpo = error.response.data as ResultadoPlantilla | string[];
      return Array.isArray(cuerpo) ? { errores: cuerpo } : cuerpo;
    }
    throw error;
  }
}
