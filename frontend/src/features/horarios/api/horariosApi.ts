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

// Franja de la tarde, solo para talleres: cinco períodos de una hora (14:00 a 19:00).
export const PERIODOS_TALLER = [
  { numero: 7, horario: "14:00–15:00" },
  { numero: 8, horario: "15:00–16:00" },
  { numero: 9, horario: "16:00–17:00" },
  { numero: 10, horario: "17:00–18:00" },
  { numero: 11, horario: "18:00–19:00" },
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
