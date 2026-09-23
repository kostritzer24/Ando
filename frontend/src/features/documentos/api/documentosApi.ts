import { http } from "@/app/http";

export interface DocumentoVerificado {
  tipo_documento: string;
  fecha: string;
  estudiante: string;
}

// RF-14 / HU-14: la única ruta pública sin sesión de todo el contrato —
// no lleva Authorization, y un código inexistente o dado de baja da 404
// sin distinción (nada de "código incorrecto" vs. "documento anulado").
export async function verificarDocumento(codigo: string): Promise<DocumentoVerificado> {
  const { data } = await http.get<DocumentoVerificado>(`/verify/${codigo}/`);
  return data;
}
