import { computed } from "vue";

import { useAuthStore } from "@/features/auth/stores/authStore";

/** Áreas de la matriz de docs/permisos-roles.md, tal como las declara
 * cada vista del backend (`area = "..."`). */
export type Area =
  | "usuarios_roles"
  | "datos_maestros"
  | "estudiantes_encargados"
  | "datos_sensibles"
  | "horarios_calendario"
  | "asistencia"
  | "notas"
  | "modificacion_notas"
  | "pagos_solvencia"
  | "documentos"
  | "avisos"
  | "reportes_conducta"
  | "buzon"
  | "reportes_institucionales"
  | "bitacora_registro_acceso";

export type Nivel = "sin_acceso" | "ver" | "editar";

export type Permisos = Partial<Record<Area, Nivel>>;

/** Qué puede hacer la persona en sesión, leído de la matriz real de su
 * rol (`/auth/me/`), no de su nombre de rol. Antes el menú y los botones
 * repetían listas de roles a mano y se desalineaban de la matriz:
 * Administrador y Coordinación no veían pantallas que la matriz les
 * concede, y Encargado de pagos veía una a la que no tiene acceso. El
 * backend sigue siendo el que decide; esto solo evita ofrecer lo que va a
 * rechazar. */
export function usePermisos() {
  const auth = useAuthStore();
  const permisos = computed<Permisos>(() => (auth.usuario?.permissions ?? {}) as Permisos);

  function nivel(area: Area): Nivel {
    return permisos.value[area] ?? "sin_acceso";
  }

  return {
    nivel,
    puedeVer: (area: Area) => nivel(area) !== "sin_acceso",
    puedeEditar: (area: Area) => nivel(area) === "editar",
  };
}
