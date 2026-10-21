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
  jornada: Jornada;
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

export type Jornada = "basicos" | "bachillerato";

export const ETIQUETA_JORNADA: Record<Jornada, string> = {
  basicos: "Primero y segundo",
  bachillerato: "Tercero a quinto",
};

/** Tercero básico, cuarto y quinto bachillerato siguen el horario de
 * bachillerato; el resto (primero y segundo básico y los talleres) el de básicos. */
export function jornadaDeGrado(grado: string): Jornada {
  const g = grado.toLowerCase();
  return g.includes("bachiller") || g.includes("tercero") ? "bachillerato" : "basicos";
}

// RN-13: seis períodos de 40 minutos de 8:00 a 12:40. Los dos horarios solo
// difieren en dónde cae el receso: básicos 10:00–10:40, bachillerato 10:40–11:20.
const HORARIO_JORNADA: Record<Jornada, Record<number, string>> = {
  basicos: {
    1: "8:00–8:40",
    2: "8:40–9:20",
    3: "9:20–10:00",
    4: "10:40–11:20",
    5: "11:20–12:00",
    6: "12:00–12:40",
  },
  bachillerato: {
    1: "8:00–8:40",
    2: "8:40–9:20",
    3: "9:20–10:00",
    4: "10:00–10:40",
    5: "11:20–12:00",
    6: "12:00–12:40",
  },
};

/** Receso de cada jornada y el período que lo sigue. */
export const RECESO_JORNADA: Record<Jornada, { antesDe: number; horario: string }> = {
  basicos: { antesDe: 4, horario: "10:00–10:40" },
  bachillerato: { antesDe: 5, horario: "10:40–11:20" },
};

/** Hora de un período para una jornada; los talleres (7 a 11) no cambian. */
export function horaDePeriodo(numero: number, jornada: Jornada = "basicos"): string {
  const taller = PERIODOS_TALLER.find((p) => p.numero === numero);
  return taller ? taller.horario : (HORARIO_JORNADA[jornada][numero] ?? "");
}

/** Períodos de la mañana con la hora del horario de básicos. */
export const PERIODOS = [1, 2, 3, 4, 5, 6].map((numero) => ({
  numero,
  horario: HORARIO_JORNADA.basicos[numero]!,
}));

export interface FilaPeriodo {
  numero: number;
  horario: string;
  /** Recesos que caen justo antes de este período (uno por jornada). */
  recesos: string[];
}

/** Filas de la cuadrícula de una persona o sección: quien da clase en las
 * dos jornadas ve las dos horas en cada período y los dos recesos. */
export function filasDePeriodos(
  jornadas: Jornada[],
  opciones: { jornada: boolean; taller: boolean },
): FilaPeriodo[] {
  const activas: Jornada[] = jornadas.length > 0 ? jornadas : ["basicos"];
  const mixto = activas.length > 1;
  const filas: FilaPeriodo[] = [];
  if (opciones.jornada) {
    for (const periodo of PERIODOS) {
      const horas = activas.map((j) => horaDePeriodo(periodo.numero, j));
      const distintas = new Set(horas).size > 1;
      filas.push({
        numero: periodo.numero,
        horario: distintas
          ? activas.map((j, i) => `${horas[i]} ${ETIQUETA_JORNADA[j].toLowerCase()}`).join(" / ")
          : horas[0]!,
        recesos: activas
          .filter((j) => RECESO_JORNADA[j].antesDe === periodo.numero)
          .map(
            (j) =>
              `Receso ${RECESO_JORNADA[j].horario}` + (mixto ? ` (${ETIQUETA_JORNADA[j].toLowerCase()})` : ""),
          ),
      });
    }
  }
  if (opciones.taller) {
    for (const periodo of PERIODOS_TALLER) {
      filas.push({ numero: periodo.numero, horario: periodo.horario, recesos: [] });
    }
  }
  return filas;
}
