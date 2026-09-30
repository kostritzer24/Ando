import { crearRecursoCrud, obtenerTodas } from "@/shared/api/resource";
import type {
  ActivityType,
  ConductRuleArticle,
  Course,
  DocumentType,
  GradingUnit,
  JustificationType,
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

// Solo para poblar el selector de maestro guía de Secciones (la
// administración de cuentas vive en features/usuarios).
export async function listarDocentesConSeccion(): Promise<Usuario[]> {
  // `/users/` incluye también las cuentas de las familias — con solo la
  // primera página (25) un docente podía quedar fuera del selector.
  const data = await obtenerTodas<Usuario>("/users/");
  return data.results.filter(
    (usuario) => usuario.is_active !== false && usuario.role_name === "Docente con sección a cargo",
  );
}
