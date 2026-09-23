import { http } from "@/app/http";
import { crearRecursoCrud } from "@/shared/api/resource";
import type { CalendarEvent, ScheduleBlock } from "@/shared/types/models";

export const scheduleBlocksApi = crearRecursoCrud<ScheduleBlock>("/schedule-blocks/");
export const calendarEventsApi = crearRecursoCrud<CalendarEvent>("/calendar-events/");

export interface BloqueHorarioPropio {
  public_id: string;
  day_of_week: string;
  period_number: number;
  course: string;
  section: string;
}

export async function obtenerMiHorario(): Promise<BloqueHorarioPropio[]> {
  const { data } = await http.get<BloqueHorarioPropio[]>("/schedule/mine/");
  return data;
}

export const DIAS = [
  { valor: "lunes", etiqueta: "Lunes" },
  { valor: "martes", etiqueta: "Martes" },
  { valor: "miercoles", etiqueta: "Miércoles" },
  { valor: "jueves", etiqueta: "Jueves" },
  { valor: "viernes", etiqueta: "Viernes" },
] as const;

// RN-13: seis períodos de 40 minutos, receso entre el 3 y el 4.
export const PERIODOS = [
  { numero: 1, horario: "8:00–8:40" },
  { numero: 2, horario: "8:40–9:20" },
  { numero: 3, horario: "9:20–10:00" },
  { numero: 4, horario: "10:40–11:20" },
  { numero: 5, horario: "11:20–12:00" },
  { numero: 6, horario: "12:00–12:40" },
] as const;
