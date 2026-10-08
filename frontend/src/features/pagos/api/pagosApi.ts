import { http } from "@/app/http";
import { crearRecursoCrud } from "@/shared/api/resource";
import type { IssuedDocument, Payment, ReportCard } from "@/shared/types/models";

export const paymentsApi = crearRecursoCrud<Payment>("/payments/");
export const issuedDocumentsApi = crearRecursoCrud<IssuedDocument>("/documents/");
export const reportCardsApi = crearRecursoCrud<ReportCard>("/report-cards/");

export interface EstadoSolvencia {
  solvente: boolean;
  tiene_beca: boolean;
  meses_pendientes: [number, number][];
}

export async function consultarSolvencia(enrollmentPublicId: string): Promise<EstadoSolvencia> {
  const { data } = await http.get<EstadoSolvencia>(`/solvency/${enrollmentPublicId}/`);
  return data;
}

function nombreDeArchivo(headers: Record<string, unknown>, porOmision: string): string {
  const disposicion = String(headers["content-disposition"] ?? "");
  const coincidencia = /filename="?([^"]+)"?/.exec(disposicion);
  return coincidencia?.[1] ?? porOmision;
}

export async function emitirConstanciaSolvencia(
  enrollmentPublicId: string,
): Promise<{ blob: Blob; nombreArchivo: string }> {
  const respuesta = await http.post(`/solvency/${enrollmentPublicId}/certificate/`, null, {
    responseType: "blob",
  });
  return {
    blob: respuesta.data as Blob,
    nombreArchivo: nombreDeArchivo(respuesta.headers, "constancia_solvencia.pdf"),
  };
}

export async function emitirDocumento(payload: {
  enrollment: string;
  document_type: string;
  custom_text?: string;
}): Promise<{ blob: Blob; nombreArchivo: string }> {
  const respuesta = await http.post("/documents/issue/", payload, { responseType: "blob" });
  return {
    blob: respuesta.data as Blob,
    nombreArchivo: nombreDeArchivo(respuesta.headers, "documento.pdf"),
  };
}

export async function descargarDocumento(
  documentPublicId: string,
): Promise<{ blob: Blob; nombreArchivo: string }> {
  const respuesta = await http.get(`/documents/${documentPublicId}/download/`, {
    responseType: "blob",
  });
  return {
    blob: respuesta.data as Blob,
    nombreArchivo: nombreDeArchivo(respuesta.headers, "documento.pdf"),
  };
}

export function descargarArchivo(blob: Blob, nombreArchivo: string): void {
  const url = URL.createObjectURL(blob);
  const enlace = document.createElement("a");
  enlace.href = url;
  enlace.download = nombreArchivo;
  enlace.click();
  URL.revokeObjectURL(url);
}

/** Abre el PDF de revisión de un boletín (borrador, aprobado o publicado)
 * en otra pestaña: Dirección lo revisa antes de aprobar. */
export async function verVistaPreviaBoletin(reportCardPublicId: string): Promise<void> {
  const respuesta = await http.get(`/report-cards/${reportCardPublicId}/preview/`, {
    responseType: "blob",
  });
  const url = URL.createObjectURL(respuesta.data as Blob);
  window.open(url, "_blank");
  setTimeout(() => URL.revokeObjectURL(url), 60_000);
}

export async function generarBoletines(payload: {
  section: string;
  unit: string;
}): Promise<ReportCard[]> {
  const { data } = await http.post<ReportCard[]>("/report-cards/generate/", payload);
  return data;
}

export async function aprobarBoletin(publicId: string): Promise<ReportCard> {
  const { data } = await http.post<ReportCard>(`/report-cards/${publicId}/approve/`);
  return data;
}

export async function publicarBoletin(publicId: string): Promise<ReportCard> {
  const { data } = await http.post<ReportCard>(`/report-cards/${publicId}/publish/`);
  return data;
}

export async function aprobarBoletinesEnLote(payload: {
  section: string;
  unit: string;
}): Promise<{ aprobados: number }> {
  const { data } = await http.post<{ aprobados: number }>("/report-cards/approve-batch/", payload);
  return data;
}

export interface ResultadoPublicacionEnLote {
  publicados: number;
  no_publicados: { estudiante: string; motivo: string }[];
}

export async function publicarBoletinesEnLote(payload: {
  section: string;
  unit: string;
}): Promise<ResultadoPublicacionEnLote> {
  const { data } = await http.post<ResultadoPublicacionEnLote>(
    "/report-cards/publish-batch/",
    payload,
  );
  return data;
}
