<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";

import { assignmentsApi } from "@/features/asignaciones/api/asignacionesApi";
import { AppButton, AppModal, CargandoBloque, DataTable, ErrorBanner, FormField, FormSelect, PageHeader } from "@/shared/components";
import type { Activity, ActivityType, GradingUnit, TeacherAssignment } from "@/shared/types/models";

import { avisar } from "@/shared/composables/useAvisos";
import { confirmar } from "@/shared/composables/useConfirmar";

import { activitiesApi, activityTypesApi, motivoDelRechazo, unidadesDeCiclo } from "../api/notasApi";

const cargando = ref(true);
const error = ref("");
const asignaciones = ref<TeacherAssignment[]>([]);
const tiposActividad = ref<ActivityType[]>([]);

const asignacionElegida = ref("");
const unidades = ref<GradingUnit[]>([]);
const unidadElegida = ref("");
const cargandoUnidades = ref(false);

const actividades = ref<Activity[]>([]);
const cargandoActividades = ref(false);

const opcionesAsignacion = computed(() =>
  asignaciones.value.map((a) => ({
    valor: a.public_id,
    etiqueta: `${a.course_name} — ${a.section_grade} ${a.section_letter}`.trim(),
  })),
);
const opcionesUnidad = computed(() =>
  unidades.value.map((u) => ({ valor: u.public_id, etiqueta: `Unidad ${u.number}` })),
);
const opcionesTipo = computed(() =>
  tiposActividad.value.map((t) => ({ valor: t.public_id, etiqueta: t.name })),
);

const puntosUsados = computed(() =>
  actividades.value.reduce((total, act) => total + Number(act.max_score), 0),
);
const puntosDisponibles = computed(() => 100 - puntosUsados.value);
// Al editar, los puntos de la propia actividad vuelven a estar disponibles.
const puntosParaElFormulario = computed(
  () => puntosDisponibles.value + (editando.value ? Number(editando.value.max_score) : 0),
);
const cantidadPruebasCortas = computed(() => {
  const idsPruebaCorta = new Set(
    tiposActividad.value.filter((t) => t.counts_as_short_quiz).map((t) => t.public_id),
  );
  return actividades.value.filter((a) => idsPruebaCorta.has(a.activity_type)).length;
});

const modalAbierto = ref(false);
const guardando = ref(false);
const editando = ref<Activity | null>(null);
const errorFormulario = ref("");
const formulario = reactive({ name: "", activity_type: "", max_score: "", due_date: "" });

async function cargarBase(): Promise<void> {
  cargando.value = true;
  error.value = "";
  try {
    const [asignacionesResp, tiposResp] = await Promise.all([
      assignmentsApi.listar(),
      activityTypesApi.listar(),
    ]);
    asignaciones.value = asignacionesResp.results;
    tiposActividad.value = tiposResp.results.filter((t) => t.is_active !== false);
    asignacionElegida.value = opcionesAsignacion.value[0]?.valor ?? "";
  } catch {
    error.value = "No se pudo cargar la información inicial. Inténtalo de nuevo.";
  } finally {
    cargando.value = false;
  }
}

async function cargarUnidades(): Promise<void> {
  const asignacion = asignaciones.value.find((a) => a.public_id === asignacionElegida.value);
  if (!asignacion) {
    unidades.value = [];
    return;
  }
  cargandoUnidades.value = true;
  try {
    unidades.value = (await unidadesDeCiclo(asignacion.cycle).listar()).results;
    unidadElegida.value = opcionesUnidad.value[0]?.valor ?? "";
  } catch {
    error.value = "No se pudieron cargar las unidades de este ciclo. Inténtalo de nuevo.";
  } finally {
    cargandoUnidades.value = false;
  }
}

async function cargarActividades(): Promise<void> {
  if (!asignacionElegida.value || !unidadElegida.value) {
    actividades.value = [];
    return;
  }
  cargandoActividades.value = true;
  error.value = "";
  try {
    const respuesta = await activitiesApi.listar({
      assignment: asignacionElegida.value,
      unit: unidadElegida.value,
    });
    actividades.value = respuesta.results.filter((a) => a.is_active !== false);
  } catch {
    error.value = "No se pudieron cargar las actividades de la unidad. Inténtalo de nuevo.";
  } finally {
    cargandoActividades.value = false;
  }
}

function abrirEdicion(actividad: Activity): void {
  editando.value = actividad;
  errorFormulario.value = "";
  formulario.name = actividad.name;
  formulario.activity_type = actividad.activity_type;
  formulario.max_score = actividad.max_score;
  formulario.due_date = actividad.due_date;
  modalAbierto.value = true;
}

async function darDeBaja(actividad: Activity): Promise<void> {
  const seguir = await confirmar({
    titulo: `¿Quitar "${actividad.name}"?`,
    mensaje: `Libera ${actividad.max_score} puntos de la unidad. Solo se puede si todavía no tiene notas.`,
    etiquetaConfirmar: "Quitar actividad",
    peligro: true,
  });
  if (!seguir) return;
  try {
    await activitiesApi.darDeBaja(actividad.public_id);
    avisar("Actividad quitada.");
    await cargarActividades();
  } catch (e) {
    error.value = motivoDelRechazo(e, "No se pudo quitar la actividad. Inténtalo de nuevo.");
  }
}

function abrirNueva(): void {
  editando.value = null;
  errorFormulario.value = "";
  formulario.name = "";
  formulario.activity_type = opcionesTipo.value[0]?.valor ?? "";
  formulario.max_score = "";
  formulario.due_date = "";
  modalAbierto.value = true;
}

async function guardar(): Promise<void> {
  guardando.value = true;
  errorFormulario.value = "";
  try {
    if (editando.value) {
      await activitiesApi.actualizar(editando.value.public_id, {
        name: formulario.name,
        activity_type: formulario.activity_type,
        max_score: formulario.max_score,
        due_date: formulario.due_date,
      });
      modalAbierto.value = false;
      avisar("Actividad actualizada.");
      await cargarActividades();
      return;
    }
    await activitiesApi.crear({
      assignment: asignacionElegida.value,
      unit: unidadElegida.value,
      activity_type: formulario.activity_type,
      name: formulario.name,
      max_score: formulario.max_score,
      due_date: formulario.due_date,
    });
    modalAbierto.value = false;
    await cargarActividades();
  } catch (e) {
    // Dentro del diálogo: el motivo real ("la unidad no puede superar los 100
    // puntos", "ya tiene notas") sin perder lo que se escribió.
    errorFormulario.value = motivoDelRechazo(e, "No se pudo guardar la actividad. Revisa los datos e inténtalo de nuevo.");
  } finally {
    guardando.value = false;
  }
}

watch(asignacionElegida, cargarUnidades);
watch([asignacionElegida, unidadElegida], cargarActividades);

onMounted(async () => {
  await cargarBase();
  await cargarUnidades();
});
</script>

<template>
  <section class="unidad-page">
    <PageHeader titulo="Diseñar la unidad" />

    <ErrorBanner v-if="error" :mensaje="error" etiqueta-accion="Reintentar" @accion="cargarActividades" />
    <CargandoBloque v-else-if="cargando" />

    <template v-else>
      <div class="unidad-page__filtros">
        <FormSelect
          id="assignment"
          etiqueta="Curso y sección"
          :opciones="opcionesAsignacion"
          v-model="asignacionElegida"
        />
        <FormSelect id="unit" etiqueta="Unidad" :opciones="opcionesUnidad" v-model="unidadElegida" />
      </div>

      <CargandoBloque v-if="cargandoUnidades || cargandoActividades" />

      <template v-else-if="unidadElegida">
        <div class="unidad-page__resumen">
          <p>
            <strong>{{ puntosUsados }}</strong> de 100 puntos usados
            ({{ puntosDisponibles }} disponibles).
          </p>
          <p :class="{ 'unidad-page__aviso': cantidadPruebasCortas < 4 }">
            {{ cantidadPruebasCortas }} de 4 pruebas cortas como mínimo.
          </p>
        </div>

        <AppButton :deshabilitado="puntosDisponibles <= 0" @click="abrirNueva">
          Agregar actividad
        </AppButton>

        <DataTable
          v-if="actividades.length > 0"
          class="unidad-page__tabla"
          :columnas="[
            { clave: 'name', etiqueta: 'Actividad' },
            { clave: 'max_score', etiqueta: 'Puntos' },
            { clave: 'due_date', etiqueta: 'Fecha de entrega' },
          ]"
          :filas="actividades"
        >
          <template #acciones="{ fila }">
            <button type="button" class="unidad-page__accion" @click="abrirEdicion(fila as unknown as Activity)">
              Editar
            </button>
            <button type="button" class="unidad-page__accion" @click="darDeBaja(fila as unknown as Activity)">
              Quitar
            </button>
          </template>
        </DataTable>
        <p v-else class="unidad-page__vacio">Todavía no hay actividades en esta unidad.</p>
      </template>

      <AppModal
        v-if="modalAbierto"
        :titulo="editando ? 'Editar actividad' : 'Agregar actividad'"
        @cerrar="modalAbierto = false"
      >
        <form class="unidad-page__formulario" @submit.prevent="guardar">
          <ErrorBanner v-if="errorFormulario" :mensaje="errorFormulario" />
          <p v-if="editando" class="unidad-page__nota">
            Si la actividad ya tiene notas, su punteo máximo no se puede cambiar.
          </p>
          <FormField id="name" etiqueta="Nombre de la actividad" v-model="formulario.name" />
          <FormSelect
            id="activity_type"
            etiqueta="Tipo"
            :opciones="opcionesTipo"
            v-model="formulario.activity_type"
          />
          <FormField
            id="max_score"
            etiqueta="Punteo máximo"
            tipo="number"
            :pista="`Quedan ${puntosParaElFormulario} puntos disponibles en esta unidad.`"
            v-model="formulario.max_score"
          />
          <FormField id="due_date" etiqueta="Fecha de entrega" tipo="date" v-model="formulario.due_date" />
          <AppButton tipo="submit" :deshabilitado="guardando">
            {{ guardando ? "Guardando…" : "Guardar" }}
          </AppButton>
        </form>
      </AppModal>
    </template>
  </section>
</template>

<style scoped>

.unidad-page__filtros {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 13rem), 1fr));
  gap: var(--espacio-md) var(--espacio-lg);
  align-items: end;
  max-width: 52rem;
}

.unidad-page__resumen {
  margin-bottom: var(--espacio-lg);
}

.unidad-page__resumen p {
  margin: 0 0 var(--espacio-2xs);
}

.unidad-page__aviso {
  color: var(--color-etiqueta-alerta-texto);
}

.unidad-page__tabla {
  margin-top: var(--espacio-lg);
}

.unidad-page__vacio {
  color: var(--color-tinta-suave);
  margin-top: var(--espacio-lg);
}

.unidad-page__accion {
  background: none;
  border: none;
  color: var(--color-accion);
  font-size: var(--texto-sm);
  font-weight: 600;
  cursor: pointer;
  padding: 0.3rem 0.5rem;
}

.unidad-page__nota {
  color: var(--color-tinta-suave);
  font-size: var(--texto-sm);
  margin: 0;
}

.unidad-page__formulario {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-lg);
}
</style>
