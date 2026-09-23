import { http } from "@/app/http";
import { crearRecursoCrud } from "@/shared/api/resource";
import type { Attendance, CalendarEvent, Grade, ReportCard } from "@/shared/types/models";

export const gradesApi = crearRecursoCrud<Grade>("/grades/");
export const attendanceApi = crearRecursoCrud<Attendance>("/attendance/");
export const reportCardsApi = crearRecursoCrud<ReportCard>("/report-cards/");

export interface BloqueSemanal {
  day_of_week: string;
  period_number: number;
  course: string;
  section: string;
  section_type: string;
  teacher: string;
}

export interface CalendarioSemanal {
  schedule: BloqueSemanal[];
  events: CalendarEvent[];
}

export async function consultarCalendarioSemanal(studentPublicId: string): Promise<CalendarioSemanal> {
  const { data } = await http.get<CalendarioSemanal>("/calendar/weekly/", {
    params: { student: studentPublicId },
  });
  return data;
}

function nombreDeArchivo(headers: Record<string, unknown>, porOmision: string): string {
  const disposicion = String(headers["content-disposition"] ?? "");
  const coincidencia = /filename="?([^"]+)"?/.exec(disposicion);
  return coincidencia?.[1] ?? porOmision;
}

export async function descargarBoletin(
  reportCardPublicId: string,
): Promise<{ blob: Blob; nombreArchivo: string }> {
  const respuesta = await http.get(`/report-cards/${reportCardPublicId}/download/`, {
    responseType: "blob",
  });
  return {
    blob: respuesta.data as Blob,
    nombreArchivo: nombreDeArchivo(respuesta.headers, "boletin.pdf"),
  };
}
