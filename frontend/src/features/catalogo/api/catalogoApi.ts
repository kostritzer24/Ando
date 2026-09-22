import { http } from "@/app/http";
import { crearRecursoCrud } from "@/shared/api/resource";
import type {
  ActivityType,
  ConductRuleArticle,
  Course,
  DocumentType,
  GradingUnit,
  JustificationType,
  Paginada,
  Scholarship,
  SchoolCycle,
  Section,
} from "@/shared/types/models";
import type { components } from "@/shared/types/api";

type Usuario = components["schemas"]["User"];

export const cursosApi = crearRecursoCrud<Course>("/courses/");
export const tiposActividadApi = crearRecursoCrud<ActivityType>("/activity-types/");
export const tiposJustificacionApi = crearRecursoCrud<JustificationType>("/justification-types/");
export const tiposDocumentoApi = crearRecursoCrud<DocumentType>("/document-types/");
export const becasApi = crearRecursoCrud<Scholarship>("/scholarships/");
export const articulosConvivenciaApi = crearRecursoCrud<ConductRuleArticle>(
  "/conduct-rule-articles/",
);
export const ciclosApi = crearRecursoCrud<SchoolCycle>("/cycles/");
export const seccionesApi = crearRecursoCrud<Section>("/sections/");

export const unidadesApi = (cicloId: string) =>
  crearRecursoCrud<GradingUnit>(`/cycles/${cicloId}/units/`);

// Solo para poblar el selector de maestro guía de Secciones — la
// administración completa de usuarios (RF-01) todavía no tiene pantalla
// propia, queda pendiente de agregar al backlog de frontend.
export async function listarDocentesConSeccion(): Promise<Usuario[]> {
  // La paginación por omisión (25) alcanza sin pedir más: el centro tiene
  // 8 docentes en total (sección 1 del prompt maestro).
  const { data } = await http.get<Paginada<Usuario>>("/users/");
  return data.results.filter((usuario) => usuario.role_name === "Docente con sección a cargo");
}
