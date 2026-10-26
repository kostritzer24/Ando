import { http } from "@/app/http";
import { nombreDeArchivo } from "@/shared/api/descargas";
import { crearRecursoCrud } from "@/shared/api/resource";
import type {
  Announcement,
  ConductReport,
  ConductReportCreate,
  Conversation,
  ConversationCreate,
  ConversationDetail,
  Message,
  Recipient,
  Section,
} from "@/shared/types/models";

export const announcementsApi = crearRecursoCrud<Announcement>("/announcements/");
export const conductReportsApi = crearRecursoCrud<ConductReport>("/conduct-reports/");
export const conversationsApi = crearRecursoCrud<Conversation>("/conversations/");

export async function crearReporteConducta(payload: ConductReportCreate): Promise<ConductReport> {
  const { data } = await http.post<ConductReport>("/conduct-reports/", payload);
  return data;
}

export async function publicarReporteConducta(publicId: string): Promise<ConductReport> {
  const { data } = await http.post<ConductReport>(`/conduct-reports/${publicId}/publish/`);
  return data;
}

/** RN-18: secciones a las que se puede dirigir un aviso, sin abrir el
 * catálogo a quien no lo administra. */
export async function seccionesParaAvisos(): Promise<Section[]> {
  const { data } = await http.get<Section[]>("/announcements/target-sections/");
  return data;
}

/** Abrir una conversación la marca como leída para quien la abre (RN-19). */
export async function abrirConversacion(publicId: string): Promise<ConversationDetail> {
  const { data } = await http.get<ConversationDetail>(`/conversations/${publicId}/`);
  return data;
}

export async function iniciarConversacion(payload: ConversationCreate): Promise<ConversationDetail> {
  const { data } = await http.post<ConversationDetail>("/conversations/", payload);
  return data;
}

export async function responderConversacion(publicId: string, content: string): Promise<Message> {
  const { data } = await http.post<Message>(`/conversations/${publicId}/reply/`, { content });
  return data;
}

/** RF-38: una fila por encargado y alumno, "Encargado / Alumno". */
export async function buscarDestinatarios(): Promise<Recipient[]> {
  const { data } = await http.get<Recipient[]>("/conversations/recipients/");
  return data;
}

export async function contarNoLeidas(): Promise<number> {
  const { data } = await http.get<{ no_leidas: number }>("/conversations/unread-count/");
  return data.no_leidas;
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
