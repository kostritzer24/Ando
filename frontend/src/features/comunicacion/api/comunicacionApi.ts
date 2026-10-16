import { http } from "@/app/http";
import { nombreDeArchivo } from "@/shared/api/descargas";
import { crearRecursoCrud } from "@/shared/api/resource";
import type { Announcement, ConductReport, ConductReportCreate, Message } from "@/shared/types/models";

export const announcementsApi = crearRecursoCrud<Announcement>("/announcements/");
export const conductReportsApi = crearRecursoCrud<ConductReport>("/conduct-reports/");
export const messagesApi = crearRecursoCrud<Message>("/messages/");

export async function crearReporteConducta(payload: ConductReportCreate): Promise<ConductReport> {
  const { data } = await http.post<ConductReport>("/conduct-reports/", payload);
  return data;
}

export async function publicarReporteConducta(publicId: string): Promise<ConductReport> {
  const { data } = await http.post<ConductReport>(`/conduct-reports/${publicId}/publish/`);
  return data;
}

export async function responderMensaje(publicId: string, content: string): Promise<Message> {
  const { data } = await http.post<Message>(`/messages/${publicId}/reply/`, { content });
  return data;
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
