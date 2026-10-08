<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";

import { assignmentsApi } from "@/features/asignaciones/api/asignacionesApi";
import { enrollmentsApi } from "@/features/estudiantes/api/estudiantesApi";
import { AppButton, AppModal, CargandoBloque, ErrorBanner, FormField, FormSelect, PageHeader } from "@/shared/components";
import { avisar } from "@/shared/composables/useAvisos";
import type { Activity, Enrollment, Grade, GradingUnit, TeacherAssignment } from "@/shared/types/models";

import {
  activitiesApi,
  corregirNota,
  enPlazoDeEntrega,
  gradesApi,
  motivoDelRechazo,
  registrarPunteo,
  solicitarModificacion,
  unidadesDeCiclo,
} from "../api/notasApi";

const cargando = ref(true);
const error = ref("");
const asignaciones = ref<TeacherAssignment[]>([]);

const asignacionElegida = ref("");
const unidadElegida = ref("");
const unidades = ref<GradingUnit[]>([]);
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
const unidadesDisponibles = computed(() =>
  unidades.value.map((u) => ({ valor: u.public_id, etiqueta: `Unidad ${u.number}` })),
);
const opcionesActividad = computed(() =>
  actividades.value.map((a) => ({ valor: a.public_id, etiqueta: `${a.name} (${a.max_score} pts)` })),
);

const actividadElegidaObj = computed(() => actividades.value.find((a) => a.public_id === actividadElegida.value));
const unidadElegidaObj = computed(() => unidades.value.find((u) => u.public_id === unidadElegida.value));
// RN-05: hasta la fecha de entrega el docente corrige directo; después, solo
// por solicitud a Dirección.
const enPlazo = computed(() => enPlazoDeEntrega(unidadElegidaObj.value));
const fechaEntrega = computed(() =>
  unidadElegidaObj.value
    ? new Date(`${unidadElegidaObj.value.grades_due_date}T00:00`).toLocaleDateString("es-GT", {
        day: "numeric",
        month: "long",
      })
    : "",
);

function notaDe(inscripcion: Enrollment): Grade | undefined {
  return notas.value.find((n) => n.enrollment === inscripcion.public_id);
}

async function cargarBase(): Promise<void> {
  cargando.value = true;
  error.value = "";
  try {
    asignaciones.value = (await assignmentsApi.listar()).results;
    asignacionElegida.value = opcionesAsignacion.value[0]?.valor ?? "";
  } catch {
    error.value = "No se pudo cargar la información inicial. Inténtalo de nuevo.";
  } finally {
    cargando.value = false;
  }
}

async function cargarUnidadesYActividades(): Promise<void> {
  const asignacion = asignaciones.value.find((a) => a.public_id === asignacionElegida.value);
  actividades.value = [];
  actividadElegida.value = "";
  if (!asignacion) {
    unidades.value = [];
    return;
  }
  unidades.value = (await unidadesDeCiclo(asignacion.cycle).listar()).results;
  unidadElegida.value = unidadesDisponibles.value[0]?.valor ?? "";
}

async function cargarActividadesDeLaUnidad(): Promise<void> {
  if (!asignacionElegida.value || !unidadElegida.value) {
    actividades.value = [];
    return;
  }
  const respuesta = await activitiesApi.listar({ assignment: asignacionElegida.value, unit: unidadElegida.value });
  actividades.value = respuesta.results.filter((a) => a.is_active !== false);
  actividadElegida.value = opcionesActividad.value[0]?.valor ?? "";
}

async function cargarRoster(): Promise<void> {
  const asignacion = asignaciones.value.find((a) => a.public_id === asignacionElegida.value);
  errorGuardado.value = "";
  if (!asignacion || !actividadElegida.value) {
    inscripciones.value = [];
    return;
  }
  cargandoRoster.value = true;
  error.value = "";
  try {
    // Solo la sección y la actividad elegidas, no todas las notas del docente.
    const [inscripcionesResp, notasResp] = await Promise.all([
      enrollmentsApi.listar({ section: asignacion.section }),
      gradesApi.listar({ activity: actividadElegida.value }),
    ]);
    inscripciones.value = inscripcionesResp.results
      .filter((i) => i.is_active !== false && i.cycle === asignacion.cycle)
      .sort((a, b) => a.student_name.localeCompare(b.student_name, "es"));
    notas.value = notasResp.results;
  } catch {
    error.value = "No se pudo cargar la lista de estudiantes. Inténtalo de nuevo.";
  } finally {
    cargandoRoster.value = false;
  }
}

async function guardarNota(inscripcion: Enrollment, valor: string): Promise<void> {
  if (!valor) return;
  guardandoPorEstudiante.value[inscripcion.public_id] = true;
  errorGuardado.value = "";
  try {
    const existente = notaDe(inscripcion);
    if (existente) {
      const corregida = await corregirNota(existente.public_id, valor);
      notas.value = notas.value.map((n) => (n.public_id === corregida.public_id ? corregida : n));
      avisar(`Nota de ${inscripcion.student_name} corregida.`);
    } else {
      const creada = await registrarPunteo({
        enrollment: inscripcion.public_id,
        activity: actividadElegida.value,
        raw_score: valor,
      });
      notas.value.push(creada);
    }
  } catch (e) {
    errorGuardado.value = motivoDelRechazo(e, "No se pudo guardar el punteo. Revisa el valor e inténtalo de nuevo.");
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
    errorCorreccion.value = motivoDelRechazo(e, "No se pudo enviar la solicitud de corrección. Inténtalo de nuevo.");
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
          :placeholder="opcionesActividad.length ? 'Elige una actividad' : 'No hay actividades en esta unidad'"
        />
      </div>

      <p v-if="actividadElegida && fechaEntrega" class="capturar-notas__plazo">
        <template v-if="enPlazo">
          Puedes corregir una nota ya guardada hasta el {{ fechaEntrega }}, fecha de entrega de notas.
        </template>
        <template v-else>
          La entrega de notas de esta unidad cerró el {{ fechaEntrega }}: para cambiar una nota,
          solicita una corrección a Dirección.
        </template>
      </p>

      <ErrorBanner v-if="errorGuardado" :mensaje="errorGuardado" />

      <CargandoBloque v-if="cargandoRoster" />
      <p v-else-if="!actividadElegida" class="capturar-notas__vacio">
        Elige una actividad para capturar el punteo.
      </p>
      <p v-else-if="inscripciones.length === 0" class="capturar-notas__vacio">
        No hay estudiantes inscritos en esta sección.
      </p>

      <ul v-else class="capturar-notas__lista">
        <li v-for="inscripcion in inscripciones" :key="inscripcion.public_id" class="capturar-notas__fila">
          <label :for="`nota-${inscripcion.public_id}`" class="capturar-notas__nombre">
            {{ inscripcion.student_name }}
          </label>

          <template v-if="notaDe(inscripcion) && !enPlazo">
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
              :id="`nota-${inscripcion.public_id}`"
              :key="notaDe(inscripcion)?.current_score ?? 'nueva'"
              type="number"
              inputmode="decimal"
              step="0.01"
              min="0"
              :max="actividadElegidaObj?.max_score"
              :value="notaDe(inscripcion)?.current_score ?? ''"
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
          El punteo original se conserva: esto crea una solicitud que Dirección debe autorizar.
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

.capturar-notas__plazo {
  color: var(--color-tinta-suave);
  font-size: var(--texto-sm);
  margin: var(--espacio-md) 0 0;
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
