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

const EXTENSION_POR_TIPO: Record<string, string> = {
  "application/pdf": ".pdf",
  "image/jpeg": ".jpg",
  "image/png": ".png",
};

export async function descargarDocumentoJustificacion(
  justificationPublicId: string,
): Promise<{ blob: Blob; nombreArchivo: string }> {
  const respuesta = await http.get(`/justifications/${justificationPublicId}/document/`, {
    responseType: "blob",
  });
  const blob = respuesta.data as Blob;
  const disposicion = String(respuesta.headers["content-disposition"] ?? "");
  // Se prefiere el nombre completo en UTF-8 (con acentos); si la cabecera
  // no llega, el nombre de respaldo lleva la extensión que corresponde al
  // tipo del archivo — sin extensión ninguna aplicación lo abre.
  const utf8 = /filename\*=UTF-8''([^;]+)/i.exec(disposicion);
  const simple = /filename="?([^";]+)"?/.exec(disposicion);
  const extension = EXTENSION_POR_TIPO[blob.type] ?? "";
  return {
    blob,
    nombreArchivo: utf8 ? decodeURIComponent(utf8[1]) : (simple?.[1] ?? `Justificación${extension}`),
  };
}

export async function marcarTodosPresentes(payload: {
  date: string;
  section?: string;
}): Promise<{ creadas: number }> {
  const { data } = await http.post<{ creadas: number }>("/attendance/mark-all-present/", payload);
  return data;
}
