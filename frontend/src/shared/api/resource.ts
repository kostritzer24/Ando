// Helper genérico de CRUD sobre un recurso REST estándar (lista paginada,
// crear, editar, baja lógica). Los componentes de presentación nunca
// llaman a axios directamente (sección 12.2 del prompt maestro) — pasan
// siempre por acá o por un cliente de `features/<feature>/api/` más
// específico cuando el endpoint no es CRUD estándar (plantillas, acciones).
import { http } from "@/app/http";
import type { Paginada } from "@/shared/types/models";

/** Forma laxa que usan los componentes de catálogo genéricos (formulario
 * dinámico armado desde configuración, sin el detalle de cada modelo). */
export interface Registro {
  public_id: string;
  is_active?: boolean;
  [clave: string]: unknown;
}

export interface RecursoGenerico {
  listar: () => Promise<Paginada<Registro>>;
  crear: (payload: Record<string, unknown>) => Promise<Registro>;
  actualizar: (id: string, payload: Record<string, unknown>) => Promise<Registro>;
  darDeBaja: (id: string) => Promise<void>;
}

/** Un `crearRecursoCrud<T>()` tipado ya cumple esta forma en los hechos
 * (mismos métodos, mismo shape) — el cast es solo para que TypeScript no
 * pelee con la varianza de `Partial<T>` frente a `Record<string, unknown>`. */
export function comoRecursoGenerico<T extends { public_id: string }>(
  recurso: ReturnType<typeof crearRecursoCrud<T>>,
): RecursoGenerico {
  return recurso as unknown as RecursoGenerico;
}

export function crearRecursoCrud<T extends { public_id: string }>(rutaBase: string) {
  return {
    async listar(params?: Record<string, string | number | boolean | undefined>): Promise<Paginada<T>> {
      const { data } = await http.get<Paginada<T>>(rutaBase, { params });
      return data;
    },
    async obtener(publicId: string): Promise<T> {
      const { data } = await http.get<T>(`${rutaBase}${publicId}/`);
      return data;
    },
    async crear(payload: Partial<T>): Promise<T> {
      const { data } = await http.post<T>(rutaBase, payload);
      return data;
    },
    async actualizar(publicId: string, payload: Partial<T>): Promise<T> {
      const { data } = await http.patch<T>(`${rutaBase}${publicId}/`, payload);
      return data;
    },
    async darDeBaja(publicId: string): Promise<void> {
      await http.delete(`${rutaBase}${publicId}/`);
    },
  };
}
