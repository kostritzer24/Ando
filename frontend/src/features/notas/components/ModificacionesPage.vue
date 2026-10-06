<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { enrollmentsApi, studentsApi } from "@/features/estudiantes/api/estudiantesApi";
import { CargandoBloque, DataTable, EmptyState, ErrorBanner, PageHeader } from "@/shared/components";
import { avisar } from "@/shared/composables/useAvisos";
import { confirmar } from "@/shared/composables/useConfirmar";
import { usePermisos } from "@/shared/permisos";
import type { Activity, Enrollment, Grade, GradeChangeRequest, Student } from "@/shared/types/models";

import {
  activitiesApi,
  gradeChangeRequestsApi,
  gradesApi,
  motivoDelRechazo,
  resolverModificacion,
} from "../api/notasApi";

const permisos = usePermisos();
const puedeResolver = computed(() => permisos.puedeEditar("modificacion_notas"));

const cargando = ref(true);
const error = ref("");
const solicitudes = ref<GradeChangeRequest[]>([]);
const notas = ref<Grade[]>([]);
const actividades = ref<Activity[]>([]);
const inscripciones = ref<Enrollment[]>([]);
const estudiantes = ref<Student[]>([]);

function contexto(solicitud: GradeChangeRequest): string {
  const nota = notas.value.find((n) => n.public_id === solicitud.grade);
  const actividad = nota ? actividades.value.find((a) => a.public_id === nota.activity) : undefined;
  const inscripcion = nota ? inscripciones.value.find((i) => i.public_id === nota.enrollment) : undefined;
  const estudiante = inscripcion ? estudiantes.value.find((e) => e.public_id === inscripcion.student) : undefined;
  const nombreEstudiante = estudiante ? `${estudiante.first_name} ${estudiante.last_name}` : "—";
  return `${nombreEstudiante} — ${actividad?.name ?? "—"}`;
}

async function cargar(): Promise<void> {
  cargando.value = true;
  error.value = "";
  try {
    const [solicitudesResp, notasResp, actividadesResp, inscripcionesResp, estudiantesResp] =
      await Promise.all([
        gradeChangeRequestsApi.listar(),
        gradesApi.listar(),
        activitiesApi.listar(),
        enrollmentsApi.listar(),
        studentsApi.listar(),
      ]);
    solicitudes.value = solicitudesResp.results;
    notas.value = notasResp.results;
    actividades.value = actividadesResp.results;
    inscripciones.value = inscripcionesResp.results;
    estudiantes.value = estudiantesResp.results;
  } catch {
    error.value = "No se pudo cargar la bandeja de solicitudes. Probá de nuevo.";
  } finally {
    cargando.value = false;
  }
}

const errorAccion = ref("");
const idEnAccion = ref("");

async function resolver(solicitud: GradeChangeRequest, aprobar: boolean): Promise<void> {
  const decidido = await confirmar({
    titulo: aprobar ? "Aprobar la corrección" : "Rechazar la corrección",
    mensaje: aprobar
      ? `La nota vigente pasa de ${solicitud.original_score} a ${solicitud.requested_score}. El punteo real se conserva.`
      : `La nota se queda en ${solicitud.original_score}.`,
    etiquetaConfirmar: aprobar ? "Aprobar" : "Rechazar",
    peligro: !aprobar,
  });
  if (!decidido) return;
  idEnAccion.value = solicitud.public_id;
  errorAccion.value = "";
  try {
    await resolverModificacion(solicitud.public_id, aprobar);
    avisar(aprobar ? "Corrección aprobada." : "Corrección rechazada.");
    await cargar();
  } catch (e) {
    // Otra persona pudo resolverla mientras tanto: se recarga para ver
    // el estado real en vez de dejar los botones de una solicitud cerrada.
    errorAccion.value = motivoDelRechazo(e, "No se pudo resolver la solicitud. Probá de nuevo.");
    await cargar();
  } finally {
    idEnAccion.value = "";
  }
}

onMounted(cargar);
</script>

<template>
  <section class="modificaciones-page">
    <PageHeader :titulo='puedeResolver ? "Solicitudes de modificación" : "Mis solicitudes de modificación"' />

    <ErrorBanner v-if="errorAccion" :mensaje="errorAccion" />
    <ErrorBanner v-if="error" :mensaje="error" etiqueta-accion="Reintentar" @accion="cargar" />
    <CargandoBloque v-else-if="cargando" />
    <EmptyState
      v-else-if="solicitudes.length === 0"
      titulo="No hay solicitudes"
      descripcion="Las solicitudes de corrección de nota van a aparecer acá."
    />

    <DataTable
      v-else
      :columnas="[
        { clave: 'contexto', etiqueta: 'Estudiante — actividad' },
        { clave: 'original_score', etiqueta: 'Nota original' },
        { clave: 'requested_score', etiqueta: 'Nota propuesta' },
        { clave: 'status', etiqueta: 'Estado' },
      ]"
      :filas="solicitudes.map((s) => ({ ...s, contexto: contexto(s) }))"
    >
      <template v-if="puedeResolver" #acciones="{ fila }">
        <template v-if="(fila as unknown as GradeChangeRequest).status === 'pendiente'">
          <button
            type="button"
            class="modificaciones-page__accion"
            :disabled="idEnAccion === (fila as unknown as GradeChangeRequest).public_id"
            @click="resolver(fila as unknown as GradeChangeRequest, true)"
          >
            Aprobar
          </button>
          <button
            type="button"
            class="modificaciones-page__accion"
            :disabled="idEnAccion === (fila as unknown as GradeChangeRequest).public_id"
            @click="resolver(fila as unknown as GradeChangeRequest, false)"
          >
            Rechazar
          </button>
        </template>
      </template>
    </DataTable>
  </section>
</template>

<style scoped>

.modificaciones-page__accion {
  background: none;
  border: none;
  color: var(--color-accion);
  font-size: var(--texto-sm);
  font-weight: 600;
  cursor: pointer;
  padding: 0.3rem 0.5rem;
}
</style>
