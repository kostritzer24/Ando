<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";

import { assignmentsApi } from "@/features/asignaciones/api/asignacionesApi";
import { useAuthStore } from "@/features/auth/stores/authStore";
import { AppButton, AppModal, CargandoBloque, DataTable, EmptyState, ErrorBanner, FormSelect, PageHeader } from "@/shared/components";
import { usePermisos } from "@/shared/permisos";
import { avisar } from "@/shared/composables/useAvisos";
import { confirmar } from "@/shared/composables/useConfirmar";
import type { CalendarEvent, TeacherAssignment } from "@/shared/types/models";

import { calendarEventsApi } from "../api/horariosApi";

const TIPO_INSTITUCIONAL = "institucional";
const TIPO_ASIGNACION_DOCENTE = "asignacion_docente";

const auth = useAuthStore();
const esDireccion = computed(() => auth.usuario?.role_name === "Dirección");
// Publicar es "editar" en Horarios y calendario (Dirección y docentes);
// Coordinación y Administrador consultan.
const permisos = usePermisos();
const puedePublicar = computed(() => permisos.puedeEditar("horarios_calendario"));

const opcionesTipo = computed(() =>
  esDireccion.value
    ? [
        { valor: TIPO_INSTITUCIONAL, etiqueta: "Institucional" },
        { valor: TIPO_ASIGNACION_DOCENTE, etiqueta: "Asignación docente" },
      ]
    : [{ valor: TIPO_ASIGNACION_DOCENTE, etiqueta: "Asignación docente" }],
);

const cargando = ref(true);
const error = ref("");
const eventos = ref<CalendarEvent[]>([]);
const asignaciones = ref<TeacherAssignment[]>([]);

const opcionesAsignacion = computed(() => [
  { valor: "", etiqueta: "Ninguna" },
  ...asignaciones.value.map((a) => ({
    valor: a.public_id,
    etiqueta: `${a.course_name} — ${a.section_grade} ${a.section_letter}`.trim(),
  })),
]);

function puedeEditar(evento: CalendarEvent): boolean {
  return esDireccion.value || evento.published_by === auth.usuario?.username;
}

async function cargar(): Promise<void> {
  cargando.value = true;
  error.value = "";
  try {
    const [eventosResp, asignacionesResp] = await Promise.all([
      calendarEventsApi.listar(),
      esDireccion.value ? Promise.resolve({ results: [] as TeacherAssignment[] }) : assignmentsApi.listar(),
    ]);
    eventos.value = eventosResp.results;
    asignaciones.value = asignacionesResp.results;
  } catch {
    error.value = "No se pudo cargar el calendario. Probá de nuevo.";
  } finally {
    cargando.value = false;
  }
}

const modalAbierto = ref(false);
const guardando = ref(false);
const editando = ref<CalendarEvent | null>(null);
const formulario = reactive<{
  title: string;
  type: CalendarEvent["type"];
  event_date: string;
  start_time: string;
  end_time: string;
  materials: string;
  assignment: string;
}>({
  title: "",
  type: TIPO_ASIGNACION_DOCENTE,
  event_date: "",
  start_time: "",
  end_time: "",
  materials: "",
  assignment: "",
});

function abrirNuevo(): void {
  editando.value = null;
  formulario.title = "";
  formulario.type = esDireccion.value ? TIPO_INSTITUCIONAL : TIPO_ASIGNACION_DOCENTE;
  formulario.event_date = "";
  formulario.start_time = "";
  formulario.end_time = "";
  formulario.materials = "";
  formulario.assignment = "";
  modalAbierto.value = true;
}

function abrirEdicion(evento: CalendarEvent): void {
  editando.value = evento;
  formulario.title = evento.title;
  formulario.type = evento.type;
  formulario.event_date = evento.event_date;
  formulario.start_time = evento.start_time;
  formulario.end_time = evento.end_time;
  formulario.materials = evento.materials ?? "";
  formulario.assignment = evento.assignment ?? "";
  modalAbierto.value = true;
}

async function guardar(): Promise<void> {
  guardando.value = true;
  error.value = "";
  const payload = {
    title: formulario.title,
    type: formulario.type,
    event_date: formulario.event_date,
    start_time: formulario.start_time,
    end_time: formulario.end_time,
    materials: formulario.materials,
    assignment: formulario.assignment || null,
  };
  try {
    if (editando.value) {
      await calendarEventsApi.actualizar(editando.value.public_id, payload);
    } else {
      await calendarEventsApi.crear(payload);
    }
    modalAbierto.value = false;
    await cargar();
  } catch {
    error.value = "No se pudo guardar el evento. Revisá los datos e intentá de nuevo.";
  } finally {
    guardando.value = false;
  }
}

async function eliminar(evento: CalendarEvent): Promise<void> {
  const confirmado = await confirmar({
    titulo: "¿Quitar este evento del calendario?",
    mensaje: "Deja de verse en el calendario de docentes y familias.",
    etiquetaConfirmar: "Quitar evento",
    peligro: true,
  });
  if (!confirmado) return;
  try {
    await calendarEventsApi.darDeBaja(evento.public_id);
    avisar("Evento quitado del calendario.");
    await cargar();
  } catch {
    avisar("No se pudo quitar el evento. Probá de nuevo.", "error");
  }
}

onMounted(cargar);
</script>

<template>
  <section class="calendario-page">
    <PageHeader titulo="Calendario">
      <template #acciones>
        <AppButton v-if="puedePublicar" @click="abrirNuevo" :deshabilitado="cargando">Publicar evento</AppButton>
      </template>
    </PageHeader>

    <ErrorBanner v-if="error" :mensaje="error" etiqueta-accion="Reintentar" @accion="cargar" />
    <CargandoBloque v-else-if="cargando" />
    <EmptyState
      v-else-if="eventos.length === 0"
      titulo="Todavía no hay eventos"
      descripcion="Publicá el primer evento del calendario."
    />

    <DataTable
      v-else
      :columnas="[
        { clave: 'event_date', etiqueta: 'Fecha' },
        { clave: 'title', etiqueta: 'Título' },
        { clave: 'type', etiqueta: 'Tipo' },
        { clave: 'published_by', etiqueta: 'Publicado por' },
      ]"
      :filas="eventos"
    >
      <template #celda-type="{ fila }">
        {{ (fila as CalendarEvent).type === "institucional" ? "Institucional" : "Asignación docente" }}
      </template>
      <template #acciones="{ fila }">
        <template v-if="puedeEditar(fila as CalendarEvent)">
          <button type="button" class="calendario-page__accion" @click="abrirEdicion(fila as CalendarEvent)">
            Editar
          </button>
          <button type="button" class="calendario-page__accion" @click="eliminar(fila as CalendarEvent)">
            Eliminar
          </button>
        </template>
      </template>
    </DataTable>

    <AppModal
      v-if="modalAbierto"
      :titulo="editando ? 'Editar evento' : 'Publicar evento'"
      @cerrar="modalAbierto = false"
    >
      <form class="calendario-page__formulario" @submit.prevent="guardar">
        <label class="calendario-page__campo">
          <span>Título</span>
          <input v-model="formulario.title" type="text" required />
        </label>
        <FormSelect id="type" etiqueta="Tipo" :opciones="opcionesTipo" v-model="formulario.type" />
        <label class="calendario-page__campo">
          <span>Fecha</span>
          <input v-model="formulario.event_date" type="date" required />
        </label>
        <label class="calendario-page__campo">
          <span>Hora de inicio</span>
          <input v-model="formulario.start_time" type="time" required />
        </label>
        <label class="calendario-page__campo">
          <span>Hora de fin</span>
          <input v-model="formulario.end_time" type="time" required />
        </label>
        <FormSelect
          v-if="opcionesAsignacion.length > 1"
          id="assignment"
          etiqueta="Asignación (opcional)"
          :opciones="opcionesAsignacion"
          v-model="formulario.assignment"
        />
        <label class="calendario-page__campo">
          <span>Materiales (opcional)</span>
          <textarea v-model="formulario.materials" rows="3"></textarea>
        </label>
        <AppButton tipo="submit" :deshabilitado="guardando">
          {{ guardando ? "Guardando…" : "Guardar" }}
        </AppButton>
      </form>
    </AppModal>
  </section>
</template>

<style scoped>


.calendario-page__accion {
  background: none;
  border: none;
  color: var(--color-accion);
  font-size: var(--texto-sm);
  font-weight: 600;
  cursor: pointer;
  margin-right: var(--espacio-md);
}

.calendario-page__formulario {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-lg);
}

.calendario-page__campo {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-xs);
  font-weight: 600;
  font-size: var(--texto-base);
}

.calendario-page__campo input,
.calendario-page__campo textarea {
  min-height: var(--area-tactil-minima);
  padding: 0 0.75rem;
  border: 1px solid var(--color-linea);
  border-radius: var(--radio-md);
  font-family: var(--fuente-cuerpo);
  font-size: var(--texto-base);
  font-weight: 400;
  background: var(--color-papel);
  color: var(--color-tinta);
}

.calendario-page__campo textarea {
  padding: 0.5rem 0.75rem;
}
</style>
