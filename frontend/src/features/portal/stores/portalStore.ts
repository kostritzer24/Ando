import { defineStore } from "pinia";
import { computed, ref } from "vue";

import { enrollmentsApi, studentsApi } from "@/features/estudiantes/api/estudiantesApi";
import type { Enrollment, Student } from "@/shared/types/models";

// HU-27: un encargado con varios estudiantes vinculados cambia entre
// ellos con un selector, sin volver a iniciar sesión — este estado vive
// acá, no en cada página, para que sobreviva la navegación entre las
// pestañas del portal.
export const usePortalStore = defineStore("portal", () => {
  const estudiantes = ref<Student[]>([]);
  const inscripciones = ref<Enrollment[]>([]);
  const estudianteSeleccionadoId = ref("");
  const cargando = ref(true);
  const error = ref("");

  const estudianteSeleccionado = computed(
    () => estudiantes.value.find((e) => e.public_id === estudianteSeleccionadoId.value) ?? null,
  );

  const inscripcionesDelSeleccionado = computed(() =>
    inscripciones.value.filter(
      (i) => i.student === estudianteSeleccionadoId.value && i.is_active !== false,
    ),
  );

  // La cabecera muestra una sola sección: la académica si tiene (todo
  // estudiante la tiene), y si además está en un taller, esa inscripción
  // aparece igual en Notas/Asistencia/Horario por su cuenta.
  const seccionPrincipal = computed(() => {
    const inscs = inscripcionesDelSeleccionado.value;
    const academica = inscs.find((i) => i.section_type === "academica") ?? inscs[0];
    if (!academica) return "";
    return `${academica.section_grade} ${academica.section_letter ?? ""}`.trim();
  });

  async function cargarEstudiantes(): Promise<void> {
    cargando.value = true;
    error.value = "";
    try {
      const [estudiantesResp, inscripcionesResp] = await Promise.all([
        studentsApi.listar(),
        enrollmentsApi.listar(),
      ]);
      estudiantes.value = estudiantesResp.results;
      inscripciones.value = inscripcionesResp.results;
      if (!estudiantes.value.some((e) => e.public_id === estudianteSeleccionadoId.value)) {
        estudianteSeleccionadoId.value = estudiantes.value[0]?.public_id ?? "";
      }
    } catch {
      error.value = "No se pudo cargar la lista de estudiantes. Probá de nuevo.";
    } finally {
      cargando.value = false;
    }
  }

  function elegirEstudiante(publicId: string): void {
    estudianteSeleccionadoId.value = publicId;
  }

  return {
    estudiantes,
    inscripciones,
    estudianteSeleccionadoId,
    estudianteSeleccionado,
    inscripcionesDelSeleccionado,
    seccionPrincipal,
    cargando,
    error,
    cargarEstudiantes,
    elegirEstudiante,
  };
});
