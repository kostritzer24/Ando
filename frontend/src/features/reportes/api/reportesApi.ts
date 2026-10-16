import { http } from "@/app/http";
import { nombreDeArchivo } from "@/shared/api/descargas";

export type FilaReporte = Record<string, unknown>;

export interface DefinicionReporte {
  ruta: string;
  titulo: string;
  filtros: ("cycle" | "section" | "unit")[];
  columnas: { clave: string; etiqueta: string }[];
}

// Espejo exacto de `titulo`/`columnas` en `apps/reports/api/views.py` — RF-15,
// sección 11 del prompt maestro: los ocho reportes institucionales.
export const REPORTES: DefinicionReporte[] = [
  {
    ruta: "grades-summary",
    titulo: "Consolidado de notas",
    filtros: ["cycle", "section"],
    columnas: [
      { clave: "student_code", etiqueta: "Código" },
      { clave: "student_name", etiqueta: "Estudiante" },
      { clave: "section", etiqueta: "Sección" },
      { clave: "course", etiqueta: "Curso" },
      { clave: "unit_1_score", etiqueta: "Unidad 1" },
      { clave: "unit_2_score", etiqueta: "Unidad 2" },
      { clave: "unit_3_score", etiqueta: "Unidad 3" },
      { clave: "unit_4_score", etiqueta: "Unidad 4" },
      { clave: "final_score", etiqueta: "Nota final" },
    ],
  },
  {
    ruta: "attendance",
    titulo: "Asistencia",
    filtros: ["cycle", "section"],
    columnas: [
      { clave: "student_code", etiqueta: "Código" },
      { clave: "student_name", etiqueta: "Estudiante" },
      { clave: "section", etiqueta: "Sección" },
      { clave: "presente", etiqueta: "Presente" },
      { clave: "ausente", etiqueta: "Ausente" },
      { clave: "justificado", etiqueta: "Justificado" },
    ],
  },
  {
    ruta: "insolvent-students",
    titulo: "Estudiantes insolventes",
    filtros: ["cycle", "section"],
    columnas: [
      { clave: "student_code", etiqueta: "Código" },
      { clave: "student_name", etiqueta: "Estudiante" },
      { clave: "section", etiqueta: "Sección" },
      { clave: "pending_months", etiqueta: "Meses pendientes" },
    ],
  },
  {
    ruta: "schedules",
    titulo: "Horarios",
    filtros: ["section"],
    columnas: [
      { clave: "section", etiqueta: "Sección" },
      { clave: "course", etiqueta: "Curso" },
      { clave: "teacher", etiqueta: "Docente" },
      { clave: "day_of_week", etiqueta: "Día" },
      { clave: "period_number", etiqueta: "Período" },
    ],
  },
  {
    ruta: "enrolled-students",
    titulo: "Estudiantes inscritos",
    filtros: ["cycle", "section"],
    columnas: [
      { clave: "student_code", etiqueta: "Código" },
      { clave: "student_name", etiqueta: "Estudiante" },
      { clave: "section", etiqueta: "Sección" },
      { clave: "cycle", etiqueta: "Ciclo" },
      { clave: "status", etiqueta: "Estado" },
      { clave: "scholarship", etiqueta: "Beca" },
    ],
  },
  {
    ruta: "grade-change-history",
    titulo: "Historial de modificaciones de notas",
    filtros: ["cycle", "section", "unit"],
    columnas: [
      { clave: "student_code", etiqueta: "Código" },
      { clave: "student_name", etiqueta: "Estudiante" },
      { clave: "course", etiqueta: "Curso" },
      { clave: "unit", etiqueta: "Unidad" },
      { clave: "original_score", etiqueta: "Nota original" },
      { clave: "requested_score", etiqueta: "Nota propuesta" },
      { clave: "reason", etiqueta: "Motivo" },
      { clave: "requested_by", etiqueta: "Solicitado por" },
      { clave: "status", etiqueta: "Estado" },
      { clave: "authorized_by", etiqueta: "Autorizado por" },
      { clave: "decided_at", etiqueta: "Fecha de decisión" },
    ],
  },
  {
    ruta: "family-access",
    titulo: "Accesos de las familias",
    filtros: [],
    columnas: [
      { clave: "user", etiqueta: "Usuario" },
      { clave: "screen_viewed", etiqueta: "Pantalla" },
      { clave: "accessed_at", etiqueta: "Fecha" },
    ],
  },
  {
    ruta: "issued-documents",
    titulo: "Documentos emitidos",
    filtros: ["cycle", "section"],
    columnas: [
      { clave: "student_code", etiqueta: "Código" },
      { clave: "student_name", etiqueta: "Estudiante" },
      { clave: "section", etiqueta: "Sección" },
      { clave: "document_type", etiqueta: "Tipo" },
      { clave: "issued_at", etiqueta: "Fecha de emisión" },
      { clave: "issued_by", etiqueta: "Emitido por" },
    ],
  },
];

export async function consultarReporte(
  ruta: string,
  params: Record<string, string>,
): Promise<FilaReporte[]> {
  const { data } = await http.get<{ results: FilaReporte[] }>(`/reports/${ruta}/`, { params });
  return data.results;
}

export async function descargarReportePdf(
  ruta: string,
  params: Record<string, string>,
): Promise<{ blob: Blob; nombreArchivo: string }> {
  const respuesta = await http.get(`/reports/${ruta}/`, {
    params: { ...params, export: "pdf" },
    responseType: "blob",
  });
  return {
    blob: respuesta.data as Blob,
    nombreArchivo: nombreDeArchivo(respuesta.headers, `${ruta}.pdf`),
  };
}

export interface Metricas {
  period_start: string;
  period_end: string;
  administrative_processes_percentage: number;
  guardians_portal_usage_percentage: number;
}

export async function consultarMetricas(): Promise<Metricas> {
  const { data } = await http.get<Metricas>("/reports/metrics/");
  return data;
}

export interface HorarioEnCuadricula {
  titulo: string;
  subtitulo: string;
  dias: { clave: string; etiqueta: string }[];
  periodos: {
    numero: number;
    hora: string;
    receso_antes: string[];
    celdas: Record<string, { curso: string; detalle: string } | null>;
  }[];
}

/** El horario de un grado (`section`) o de una persona (`teacher`) como
 * cuadrícula de días × períodos. */
export async function consultarHorarioEnCuadricula(
  sujeto: { section: string } | { teacher: string },
): Promise<HorarioEnCuadricula> {
  const { data } = await http.get<HorarioEnCuadricula>("/reports/schedule-grid/", { params: sujeto });
  return data;
}

export async function descargarHorarioPdf(
  sujeto: { section: string } | { teacher: string },
): Promise<{ blob: Blob; nombreArchivo: string }> {
  const respuesta = await http.get("/reports/schedule-grid/", {
    params: { ...sujeto, export: "pdf" },
    responseType: "blob",
  });
  return {
    blob: respuesta.data as Blob,
    nombreArchivo: nombreDeArchivo(respuesta.headers, "horario.pdf"),
  };
}
