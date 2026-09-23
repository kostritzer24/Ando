import { http } from "@/app/http";
import { crearRecursoCrud } from "@/shared/api/resource";
import type { Announcement, ConductReport, ConductReportCreate, Message } from "@/shared/types/models";

export const announcementsApi = crearRecursoCrud<Announcement>("/announcements/");
export const conductReportsApi = crearRecursoCrud<ConductReport>("/conduct-reports/");
export const messagesApi = crearRecursoCrud<Message>("/messages/");

export async function crearReporteConducta(payload: ConductReportCreate): Promise<ConductReport> {
  const { data } = await http.post<ConductReport>("/conduct-reports/", payload);
  return data;
}

export async function responderMensaje(publicId: string, content: string): Promise<Message> {
  const { data } = await http.post<Message>(`/messages/${publicId}/reply/`, { content });
  return data;
}

function nombreDeArchivo(headers: Record<string, unknown>, porOmision: string): string {
  const disposicion = String(headers["content-disposition"] ?? "");
  const coincidencia = /filename="?([^"]+)"?/.exec(disposicion);
  return coincidencia?.[1] ?? porOmision;
}

export async function descargarReporteConducta(
  publicId: string,
): Promise<{ blob: Blob; nombreArchivo: string }> {
  const respuesta = await http.get(`/conduct-reports/${publicId}/download/`, { responseType: "blob" });
  return {
    blob: respuesta.data as Blob,
    nombreArchivo: nombreDeArchivo(respuesta.headers, "reporte_conducta.pdf"),
  };
}
