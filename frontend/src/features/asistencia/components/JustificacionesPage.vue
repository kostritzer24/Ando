<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";

import { useAuthStore } from "@/features/auth/stores/authStore";
import { tiposJustificacionApi } from "@/features/catalogo/api/catalogoApi";
import { enrollmentsApi, studentsApi } from "@/features/estudiantes/api/estudiantesApi";
import { AppButton, AppModal, DataTable, EmptyState, ErrorBanner, FormSelect } from "@/shared/components";
import type { Attendance, Enrollment, Justification, JustificationType, Student } from "@/shared/types/models";

import {
  attendanceApi,
  crearJustificacion,
  descargarDocumentoJustificacion,
  justificationsApi,
  resolverJustificacion,
} from "../api/asistenciaApi";

const auth = useAuthStore();
const puedeResolver = computed(() => auth.usuario?.role_name === "Dirección");

const cargando = ref(true);
const error = ref("");
const justificaciones = ref<Justification[]>([]);
const asistencias = ref<Attendance[]>([]);
const inscripciones = ref<Enrollment[]>([]);
const estudiantes = ref<Student[]>([]);
const tiposJustificacion = ref<JustificationType[]>([]);

const modalAbierto = ref(false);
const guardando = ref(false);
const archivoElegido = ref<File | null>(null);
const formulario = reactive({ attendance: "", justification_type: "", reason_detail: "" });

function estudianteDeInscripcion(enrollmentPublicId: string): string {
  const inscripcion = inscripciones.value.find((i) => i.public_id === enrollmentPublicId);
  if (!inscripcion) return "—";
  const est = estudiantes.value.find((e) => e.public_id === inscripcion.student);
  return est ? `${est.first_name} ${est.last_name}` : "—";
}

function descripcionAsistencia(asistencia: Attendance): string {
  return `${estudianteDeInscripcion(asistencia.enrollment)} — ${asistencia.date} — ${asistencia.status}`;
}

const opcionesAsistencia = computed(() =>
  asistencias.value
    .filter((a) => a.status === "ausente" || a.status === "tarde")
    .map((a) => ({ valor: a.public_id, etiqueta: descripcionAsistencia(a) })),
);
const opcionesTipo = computed(() =>
  tiposJustificacion.value.map((t) => ({ valor: t.public_id, etiqueta: t.name })),
);

function nombreEstudianteDeJustificacion(justificacion: Justification): string {
  const asistencia = asistencias.value.find((a) => a.public_id === justificacion.attendance);
  return asistencia ? estudianteDeInscripcion(asistencia.enrollment) : "—";
}
function fechaDeJustificacion(justificacion: Justification): string {
  return asistencias.value.find((a) => a.public_id === justificacion.attendance)?.date ?? "—";
}

async function cargar(): Promise<void> {
  cargando.value = true;
  error.value = "";
  try {
    const [justResp, asisResp, inscResp, estResp, tiposResp] = await Promise.all([
      justificationsApi.listar(),
      attendanceApi.listar(),
      enrollmentsApi.listar(),
      studentsApi.listar(),
      tiposJustificacionApi.listar(),
    ]);
    justificaciones.value = justResp.results;
    asistencias.value = asisResp.results;
    inscripciones.value = inscResp.results;
    estudiantes.value = estResp.results;
    tiposJustificacion.value = tiposResp.results.filter((t) => t.is_active !== false);
  } catch {
    error.value = "No se pudo cargar la información. Probá de nuevo.";
  } finally {
    cargando.value = false;
  }
}

function abrirNueva(): void {
  formulario.attendance = opcionesAsistencia.value[0]?.valor ?? "";
  formulario.justification_type = tiposJustificacion.value[0]?.public_id ?? "";
  formulario.reason_detail = "";
  archivoElegido.value = null;
  modalAbierto.value = true;
}

function alElegirArchivo(evento: Event): void {
  archivoElegido.value = (evento.target as HTMLInputElement).files?.[0] ?? null;
}

async function guardar(): Promise<void> {
  guardando.value = true;
  error.value = "";
  try {
    await crearJustificacion({
      attendance: formulario.attendance,
      justification_type: formulario.justification_type,
      reason_detail: formulario.reason_detail,
      supporting_document: archivoElegido.value ?? undefined,
    });
    modalAbierto.value = false;
    await cargar();
  } catch {
    error.value = "No se pudo registrar la justificación. Revisá los datos e intentá de nuevo.";
  } finally {
    guardando.value = false;
  }
}

async function resolver(justificacion: Justification, aprobar: boolean): Promise<void> {
  await resolverJustificacion(justificacion.public_id, aprobar);
  await cargar();
}

async function descargar(justificacion: Justification): Promise<void> {
  const { blob, nombreArchivo } = await descargarDocumentoJustificacion(justificacion.public_id);
  const url = URL.createObjectURL(blob);
  const enlace = document.createElement("a");
  enlace.href = url;
  enlace.download = nombreArchivo;
  enlace.click();
  URL.revokeObjectURL(url);
}

onMounted(cargar);
</script>

<template>
  <section class="justificaciones-page">
    <header class="justificaciones-page__cabecera">
      <h1>Justificaciones</h1>
      <AppButton @click="abrirNueva">Registrar justificación</AppButton>
    </header>

    <ErrorBanner v-if="error" :mensaje="error" etiqueta-accion="Reintentar" @accion="cargar" />
    <p v-else-if="cargando">Cargando…</p>
    <EmptyState
      v-else-if="justificaciones.length === 0"
      titulo="Todavía no hay justificaciones"
      descripcion="Las justificaciones que se registren van a aparecer acá."
    />

    <DataTable
      v-else
      :columnas="[
        { clave: 'estudiante', etiqueta: 'Estudiante' },
        { clave: 'fecha', etiqueta: 'Fecha' },
        { clave: 'resolution', etiqueta: 'Estado' },
      ]"
      :filas="justificaciones.map((j) => ({ ...j, estudiante: nombreEstudianteDeJustificacion(j), fecha: fechaDeJustificacion(j) }))"
    >
      <template #acciones="{ fila }">
        <button
          v-if="(fila as unknown as Justification).has_supporting_document"
          type="button"
          class="justificaciones-page__accion"
          @click="descargar(fila as unknown as Justification)"
        >
          Descargar documento
        </button>
        <template v-if="puedeResolver && (fila as unknown as Justification).resolution === 'pendiente'">
          <button
            type="button"
            class="justificaciones-page__accion"
            @click="resolver(fila as unknown as Justification, true)"
          >
            Aprobar
          </button>
          <button
            type="button"
            class="justificaciones-page__accion"
            @click="resolver(fila as unknown as Justification, false)"
          >
            Rechazar
          </button>
        </template>
      </template>
    </DataTable>

    <AppModal v-if="modalAbierto" titulo="Registrar justificación" @cerrar="modalAbierto = false">
      <form class="justificaciones-page__formulario" @submit.prevent="guardar">
        <FormSelect
          id="attendance"
          etiqueta="Falta a justificar"
          :opciones="opcionesAsistencia"
          v-model="formulario.attendance"
        />
        <FormSelect
          id="justification_type"
          etiqueta="Tipo de justificación"
          :opciones="opcionesTipo"
          v-model="formulario.justification_type"
        />
        <div class="justificaciones-page__campo">
          <label for="reason_detail">Motivo</label>
          <textarea id="reason_detail" rows="3" v-model="formulario.reason_detail" />
        </div>
        <div class="justificaciones-page__campo">
          <label for="supporting_document">Documento de respaldo (opcional)</label>
          <input id="supporting_document" type="file" @change="alElegirArchivo" />
        </div>
        <AppButton tipo="submit" :deshabilitado="guardando || opcionesAsistencia.length === 0">
          {{ guardando ? "Guardando…" : "Guardar" }}
        </AppButton>
        <p v-if="opcionesAsistencia.length === 0" class="justificaciones-page__nota">
          No hay faltas o tardanzas propias sin justificar todavía.
        </p>
      </form>
    </AppModal>
  </section>
</template>

<style scoped>
.justificaciones-page__cabecera {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--espacio-xl);
}

.justificaciones-page__cabecera h1 {
  font-family: var(--fuente-titulo);
  font-size: var(--texto-md);
  margin: 0;
}

.justificaciones-page__accion {
  background: none;
  border: none;
  color: var(--color-accion);
  font-size: var(--texto-sm);
  font-weight: 600;
  cursor: pointer;
  padding: 0.3rem 0.5rem;
}

.justificaciones-page__formulario {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-lg);
}

.justificaciones-page__campo {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-xs);
}

.justificaciones-page__campo textarea {
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--color-linea);
  border-radius: var(--radio-md);
  font-family: var(--fuente-cuerpo);
  font-size: var(--texto-base);
  resize: vertical;
}

.justificaciones-page__nota {
  color: var(--color-tinta-suave);
  font-size: var(--texto-sm);
  margin: 0;
}
</style>
