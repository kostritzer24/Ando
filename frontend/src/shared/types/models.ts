// Alias cortos sobre los tipos generados en `api.ts` (sección 12.3 del
// prompt maestro: los tipos de TypeScript se generan desde el esquema
// OpenAPI, no se escriben a mano — ver `npm run types:generate`).
import type { components } from "./api";

export type SchoolCycle = components["schemas"]["SchoolCycle"];
export type GradingUnit = components["schemas"]["GradingUnit"];
export type Section = components["schemas"]["Section"];
export type Course = components["schemas"]["Course"];
export type ActivityType = components["schemas"]["ActivityType"];
export type JustificationType = components["schemas"]["JustificationType"];
export type DocumentType = components["schemas"]["DocumentType"];
export type Scholarship = components["schemas"]["Scholarship"];
export type ConductRuleArticle = components["schemas"]["ConductRuleArticle"];

export type Student = components["schemas"]["Student"];
export type Guardian = components["schemas"]["Guardian"];
export type Enrollment = components["schemas"]["Enrollment"];

export type TeacherAssignment = components["schemas"]["TeacherAssignment"];
export type ScheduleBlock = components["schemas"]["ScheduleBlock"];
export type CalendarEvent = components["schemas"]["CalendarEvent"];

export type Attendance = components["schemas"]["Attendance"];
export type Justification = components["schemas"]["Justification"];

export type Activity = components["schemas"]["Activity"];
export type Grade = components["schemas"]["Grade"];
export type GradeChangeRequest = components["schemas"]["GradeChangeRequest"];
export type ReportCard = components["schemas"]["ReportCard"];

export type Payment = components["schemas"]["Payment"];
export type IssuedDocument = components["schemas"]["IssuedDocument"];

/** Forma común de toda lista paginada del backend (`PageNumberPagination`). */
export interface Paginada<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
