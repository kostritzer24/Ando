<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";

import { assignmentsApi } from "@/features/asignaciones/api/asignacionesApi";
import { enrollmentsApi, studentsApi } from "@/features/estudiantes/api/estudiantesApi";
import { AppButton, AppModal, CargandoBloque, ErrorBanner, FormField, FormSelect, PageHeader } from "@/shared/components";
import { avisar } from "@/shared/composables/useAvisos";
import type { Activity, Enrollment, Grade, Student, TeacherAssignment } from "@/shared/types/models";

import {
  activitiesApi,
  gradesApi,
  motivoDelRechazo,
  registrarPunteo,
  solicitarModificacion,
  unidadesDeCiclo,
} from "../api/notasApi";

const cargando = ref(true);
const error = ref("");
const asignaciones = ref<TeacherAssignment[]>([]);
const estudiantes = ref<Student[]>([]);

const asignacionElegida = ref("");
const unidadElegida = ref("");
const unidadesDisponibles = ref<{ valor: string; etiqueta: string }[]>([]);
const actividades = ref<Activity[]>([]);
const actividadElegida = ref("");

const inscripciones = ref<Enrollment[]>([]);
const notas = ref<Grade[]>([]);
const cargandoRoster = ref(false);
const guardandoPorEstudiante = ref<Record<string, boolean>>({});
// Un punteo rechazado no esconde la lista (como sí lo hace un error de
// carga): el resto de la sección sigue a la vista y se puede seguir.
const errorGuardado = ref("");

const opcionesAsignacion = computed(() =>
  asignaciones.value.map((a) => ({
    valor: a.public_id,
    etiqueta: `${a.course_name} — ${a.section_grade} ${a.section_letter}`.trim(),
  })),
);
const opcionesActividad = computed(() =>
  actividades.value.map((a) => ({ valor: a.public_id, etiqueta: `${a.name} (${a.max_score} pts)` })),
);

const actividadElegidaObj = computed(() => actividades.value.find((a) => a.public_id === actividadElegida.value));

function nombreEstudiante(studentPublicId: string): string {
  const est = estudiantes.value.find((e) => e.public_id === studentPublicId);
  return est ? `${est.first_name} ${est.last_name}` : "—";
}
function notaDe(inscripcion: Enrollment): Grade | undefined {
  return notas.value.find(
    (n) => n.enrollment === inscripcion.public_id && n.activity === actividadElegida.value,
  );
}

async function cargarBase(): Promise<void> {
  cargando.value = true;
  error.value = "";
  try {
    const [asignacionesResp, estudiantesResp] = await Promise.all([
      assignmentsApi.listar(),
      studentsApi.listar(),
    ]);
    asignaciones.value = asignacionesResp.results;
    estudiantes.value = estudiantesResp.results;
    asignacionElegida.value = opcionesAsignacion.value[0]?.valor ?? "";
  } catch {
    error.value = "No se pudo cargar la información inicial. Probá de nuevo.";
  } finally {
    cargando.value = false;
  }
}

async function cargarUnidadesYActividades(): Promise<void> {
  const asignacion = asignaciones.value.find((a) => a.public_id === asignacionElegida.value);
  actividades.value = [];
  actividadElegida.value = "";
  if (!asignacion) {
    unidadesDisponibles.value = [];
    return;
  }
  const unidades = (await unidadesDeCiclo(asignacion.cycle).listar()).results;
  unidadesDisponibles.value = unidades.map((u) => ({ valor: u.public_id, etiqueta: `Unidad ${u.number}` }));
  unidadElegida.value = unidadesDisponibles.value[0]?.valor ?? "";
}

async function cargarActividadesDeLaUnidad(): Promise<void> {
  if (!asignacionElegida.value || !unidadElegida.value) {
    actividades.value = [];
    return;
  }
  const todas = (await activitiesApi.listar()).results;
  actividades.value = todas.filter(
    (a) =>
      a.assignment === asignacionElegida.value &&
      a.unit === unidadElegida.value &&
      a.is_active !== false,
  );
  actividadElegida.value = opcionesActividad.value[0]?.valor ?? "";
}

async function cargarRoster(): Promise<void> {
  const asignacion = asignaciones.value.find((a) => a.public_id === asignacionElegida.value);
  if (!asignacion || !actividadElegida.value) {
    inscripciones.value = [];
    return;
  }
  cargandoRoster.value = true;
  error.value = "";
  try {
    const [inscripcionesResp, notasResp] = await Promise.all([
      enrollmentsApi.listar(),
      gradesApi.listar(),
    ]);
    inscripciones.value = inscripcionesResp.results.filter(
      (i) => i.section === asignacion.section && i.is_active !== false,
    );
    notas.value = notasResp.results;
  } catch {
    error.value = "No se pudo cargar la lista de estudiantes. Probá de nuevo.";
  } finally {
    cargandoRoster.value = false;
  }
}

async function guardarNota(inscripcion: Enrollment, valor: string): Promise<void> {
  if (!valor) return;
  guardandoPorEstudiante.value[inscripcion.public_id] = true;
  errorGuardado.value = "";
  try {
    const creada = await registrarPunteo({
      enrollment: inscripcion.public_id,
      activity: actividadElegida.value,
      raw_score: valor,
    });
    notas.value.push(creada);
  } catch (e) {
    errorGuardado.value = motivoDelRechazo(e, "No se pudo guardar el punteo. Revisá el valor e intentá de nuevo.");
  } finally {
    guardandoPorEstudiante.value[inscripcion.public_id] = false;
  }
}

const modalCorreccionAbierto = ref(false);
const notaCorrigiendo = ref<Grade | null>(null);
const guardandoCorreccion = ref(false);
const errorCorreccion = ref("");
const formularioCorreccion = reactive({ requested_score: "", reason: "" });

function abrirCorreccion(nota: Grade): void {
  notaCorrigiendo.value = nota;
  formularioCorreccion.requested_score = "";
  formularioCorreccion.reason = "";
  errorCorreccion.value = "";
  modalCorreccionAbierto.value = true;
}

async function guardarCorreccion(): Promise<void> {
  if (!notaCorrigiendo.value) return;
  guardandoCorreccion.value = true;
  errorCorreccion.value = "";
  try {
    await solicitarModificacion({
      grade: notaCorrigiendo.value.public_id,
      requested_score: formularioCorreccion.requested_score,
      reason: formularioCorreccion.reason,
    });
    modalCorreccionAbierto.value = false;
    avisar("Solicitud enviada. Dirección tiene que autorizarla.");
  } catch (e) {
    errorCorreccion.value = motivoDelRechazo(e, "No se pudo enviar la solicitud de corrección. Probá de nuevo.");
  } finally {
    guardandoCorreccion.value = false;
  }
}

watch(asignacionElegida, cargarUnidadesYActividades);
watch(unidadElegida, cargarActividadesDeLaUnidad);
watch(actividadElegida, cargarRoster);

onMounted(async () => {
  await cargarBase();
  await cargarUnidadesYActividades();
});
</script>

<template>
  <section class="capturar-notas">
    <PageHeader titulo="Capturar notas" />

    <ErrorBanner v-if="error" :mensaje="error" etiqueta-accion="Reintentar" @accion="cargarRoster" />
    <CargandoBloque v-else-if="cargando" />

    <template v-else>
      <div class="capturar-notas__filtros">
        <FormSelect
          id="assignment"
          etiqueta="Curso y sección"
          :opciones="opcionesAsignacion"
          v-model="asignacionElegida"
        />
        <FormSelect id="unit" etiqueta="Unidad" :opciones="unidadesDisponibles" v-model="unidadElegida" />
        <FormSelect
          id="activity"
          etiqueta="Actividad"
          :opciones="opcionesActividad"
          v-model="actividadElegida"
          :placeholder="opcionesActividad.length ? 'Elegí una actividad' : 'No hay actividades en esta unidad'"
        />
      </div>

      <ErrorBanner v-if="errorGuardado" :mensaje="errorGuardado" />

      <CargandoBloque v-if="cargandoRoster" />
      <p v-else-if="!actividadElegida" class="capturar-notas__vacio">
        Elegí una actividad para capturar el punteo.
      </p>
      <p v-else-if="inscripciones.length === 0" class="capturar-notas__vacio">
        No hay estudiantes inscritos en esta sección.
      </p>

      <ul v-else class="capturar-notas__lista">
        <li v-for="inscripcion in inscripciones" :key="inscripcion.public_id" class="capturar-notas__fila">
          <span class="capturar-notas__nombre">{{ nombreEstudiante(inscripcion.student) }}</span>

          <template v-if="notaDe(inscripcion)">
            <span class="capturar-notas__nota-vigente">
              {{ notaDe(inscripcion)?.current_score }} / {{ actividadElegidaObj?.max_score }}
            </span>
            <button
              type="button"
              class="capturar-notas__accion"
              @click="abrirCorreccion(notaDe(inscripcion)!)"
            >
              Solicitar corrección
            </button>
          </template>
          <template v-else>
            <input
              type="number"
              step="0.01"
              class="capturar-notas__input"
              :disabled="guardandoPorEstudiante[inscripcion.public_id]"
              @change="guardarNota(inscripcion, ($event.target as HTMLInputElement).value)"
            />
            <span class="capturar-notas__max">/ {{ actividadElegidaObj?.max_score }}</span>
          </template>
        </li>
      </ul>
    </template>

    <AppModal
      v-if="modalCorreccionAbierto"
      titulo="Solicitar corrección"
      @cerrar="modalCorreccionAbierto = false"
    >
      <form class="capturar-notas__formulario-correccion" @submit.prevent="guardarCorreccion">
        <p class="capturar-notas__nota">
          El punteo real nunca se sobrescribe (RN-05) — esto crea una solicitud que Dirección
          tiene que autorizar.
        </p>
        <ErrorBanner v-if="errorCorreccion" :mensaje="errorCorreccion" />
        <FormField
          id="requested_score"
          etiqueta="Nota propuesta"
          tipo="number"
          v-model="formularioCorreccion.requested_score"
        />
        <div class="capturar-notas__campo">
          <label for="reason">Motivo</label>
          <textarea id="reason" rows="3" v-model="formularioCorreccion.reason" />
        </div>
        <AppButton tipo="submit" :deshabilitado="guardandoCorreccion">
          {{ guardandoCorreccion ? "Enviando…" : "Enviar solicitud" }}
        </AppButton>
      </form>
    </AppModal>
  </section>
</template>

<style scoped>

.capturar-notas__filtros {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 13rem), 1fr));
  gap: var(--espacio-md) var(--espacio-lg);
  align-items: end;
  max-width: 52rem;
}

.capturar-notas__vacio {
  color: var(--color-tinta-suave);
}

.capturar-notas__lista {
  list-style: none;
  padding: 0;
  margin: 0;
}

.capturar-notas__fila {
  display: flex;
  align-items: center;
  gap: var(--espacio-lg);
  padding: var(--espacio-md) 0;
  border-bottom: 1px solid var(--color-linea);
}

.capturar-notas__nombre {
  flex: 1;
  font-weight: 600;
}

.capturar-notas__nota-vigente {
  font-variant-numeric: tabular-nums;
}

.capturar-notas__input {
  width: 5rem;
  min-height: var(--area-tactil-minima);
  padding: 0 0.5rem;
  border: 1px solid var(--color-linea);
  border-radius: var(--radio-sm);
}

.capturar-notas__max {
  color: var(--color-tinta-suave);
  font-size: var(--texto-sm);
}

.capturar-notas__accion {
  background: none;
  border: none;
  color: var(--color-accion);
  font-size: var(--texto-sm);
  font-weight: 600;
  cursor: pointer;
}

.capturar-notas__formulario-correccion {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-lg);
}

.capturar-notas__nota {
  color: var(--color-tinta-suave);
  font-size: var(--texto-sm);
  margin: 0;
}

.capturar-notas__campo {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-xs);
}

.capturar-notas__campo textarea {
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--color-linea);
  border-radius: var(--radio-md);
  resize: vertical;
}
</style>
