<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { AppButton, AppModal, CargandoBloque, DataTable, EmptyState, ErrorBanner, PageHeader } from "@/shared/components";
import { avisar } from "@/shared/composables/useAvisos";
import { confirmar } from "@/shared/composables/useConfirmar";
import { usePermisos } from "@/shared/permisos";
import type { GradeChangeRequest } from "@/shared/types/models";

import { gradeChangeRequestsApi, motivoDelRechazo, resolverModificacion } from "../api/notasApi";

const permisos = usePermisos();
const puedeResolver = computed(() => permisos.puedeEditar("modificacion_notas"));

const ESTADOS: Record<string, string> = {
  pendiente: "Pendiente",
  aprobada: "Aprobada",
  rechazada: "Rechazada",
};

const cargando = ref(true);
const error = ref("");
const solicitudes = ref<GradeChangeRequest[]>([]);
const errorAccion = ref("");
const idEnAccion = ref("");

// El backend trae estudiante, curso, actividad y nota vigente con cada
// solicitud: no hace falta descargar notas, actividades, inscripciones y
// estudiantes completos para armar una línea de contexto.
const filas = computed(() =>
  solicitudes.value.map((s) => ({
    ...s,
    contexto: `${s.student_name} — ${s.course_name}, unidad ${s.unit_number}: ${s.activity_name}`,
    estado: ESTADOS[s.status ?? ""] ?? s.status,
  })),
);

async function cargar(): Promise<void> {
  cargando.value = true;
  error.value = "";
  try {
    solicitudes.value = (await gradeChangeRequestsApi.listar()).results;
  } catch {
    error.value = "No se pudo cargar la bandeja de solicitudes. Probá de nuevo.";
  } finally {
    cargando.value = false;
  }
}

async function resolver(solicitud: GradeChangeRequest, aprobar: boolean, motivo = ""): Promise<boolean> {
  idEnAccion.value = solicitud.public_id;
  errorAccion.value = "";
  try {
    await resolverModificacion(solicitud.public_id, aprobar, motivo);
    avisar(aprobar ? "Corrección aprobada." : "Corrección rechazada.");
    await cargar();
    return true;
  } catch (e) {
    // Otra persona pudo resolverla mientras tanto: se recarga para ver
    // el estado real en vez de dejar los botones de una solicitud cerrada.
    errorAccion.value = motivoDelRechazo(e, "No se pudo resolver la solicitud. Probá de nuevo.");
    await cargar();
    return false;
  } finally {
    idEnAccion.value = "";
  }
}

async function aprobar(solicitud: GradeChangeRequest): Promise<void> {
  const decidido = await confirmar({
    titulo: "Aprobar la corrección",
    mensaje: `La nota vigente pasa de ${solicitud.original_score} a ${solicitud.requested_score}. El punteo real se conserva.`,
    etiquetaConfirmar: "Aprobar",
  });
  if (decidido) await resolver(solicitud, true);
}

// Rechazar pide el motivo: el docente lo ve en su bandeja.
const rechazando = ref<GradeChangeRequest | null>(null);
const motivoRechazo = ref("");
const errorRechazo = ref("");

function abrirRechazo(solicitud: GradeChangeRequest): void {
  rechazando.value = solicitud;
  motivoRechazo.value = "";
  errorRechazo.value = "";
}

async function confirmarRechazo(): Promise<void> {
  if (!rechazando.value) return;
  if (!motivoRechazo.value.trim()) {
    errorRechazo.value = "Escribí por qué se rechaza; el docente lo va a ver.";
    return;
  }
  const solicitud = rechazando.value;
  rechazando.value = null;
  await resolver(solicitud, false, motivoRechazo.value.trim());
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
        { clave: 'original_score', etiqueta: 'Nota al pedirla' },
        { clave: 'requested_score', etiqueta: 'Nota propuesta' },
        { clave: 'reason', etiqueta: 'Motivo' },
        { clave: 'estado', etiqueta: 'Estado' },
        { clave: 'resolution_note', etiqueta: 'Respuesta de Dirección' },
      ]"
      :filas="filas"
    >
      <template v-if="puedeResolver" #acciones="{ fila }">
        <template v-if="(fila as unknown as GradeChangeRequest).status === 'pendiente'">
          <button
            type="button"
            class="modificaciones-page__accion"
            :disabled="idEnAccion === (fila as unknown as GradeChangeRequest).public_id"
            @click="aprobar(fila as unknown as GradeChangeRequest)"
          >
            Aprobar
          </button>
          <button
            type="button"
            class="modificaciones-page__accion"
            :disabled="idEnAccion === (fila as unknown as GradeChangeRequest).public_id"
            @click="abrirRechazo(fila as unknown as GradeChangeRequest)"
          >
            Rechazar
          </button>
        </template>
      </template>
    </DataTable>

    <AppModal v-if="rechazando" titulo="Rechazar la corrección" @cerrar="rechazando = null">
      <form class="modificaciones-page__formulario" @submit.prevent="confirmarRechazo">
        <p class="modificaciones-page__nota">
          {{ rechazando.student_name }} — {{ rechazando.activity_name }}: la nota se queda en
          {{ rechazando.current_score }}.
        </p>
        <ErrorBanner v-if="errorRechazo" :mensaje="errorRechazo" />
        <div class="modificaciones-page__campo">
          <label for="motivo-rechazo">Motivo del rechazo</label>
          <textarea id="motivo-rechazo" v-model="motivoRechazo" rows="3" maxlength="500" />
        </div>
        <AppButton tipo="submit" variante="peligro">Rechazar</AppButton>
      </form>
    </AppModal>
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

.modificaciones-page__formulario {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-lg);
}

.modificaciones-page__nota {
  color: var(--color-tinta-suave);
  margin: 0;
}

.modificaciones-page__campo {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-xs);
}

.modificaciones-page__campo textarea {
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--color-borde-campo);
  border-radius: var(--radio-md);
  resize: vertical;
}
</style>
