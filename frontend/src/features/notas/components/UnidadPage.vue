<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";

import { assignmentsApi } from "@/features/asignaciones/api/asignacionesApi";
import { AppButton, AppModal, CargandoBloque, DataTable, ErrorBanner, FormField, FormSelect, PageHeader } from "@/shared/components";
import type { Activity, ActivityType, GradingUnit, TeacherAssignment } from "@/shared/types/models";

import { activitiesApi, activityTypesApi, unidadesDeCiclo } from "../api/notasApi";

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
const cantidadPruebasCortas = computed(() => {
  const idsPruebaCorta = new Set(
    tiposActividad.value.filter((t) => t.counts_as_short_quiz).map((t) => t.public_id),
  );
  return actividades.value.filter((a) => idsPruebaCorta.has(a.activity_type)).length;
});

const modalAbierto = ref(false);
const guardando = ref(false);
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
    error.value = "No se pudo cargar la información inicial. Probá de nuevo.";
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
    error.value = "No se pudieron cargar las unidades de este ciclo. Probá de nuevo.";
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
    const todas = (await activitiesApi.listar()).results;
    actividades.value = todas.filter(
      (a) =>
        a.assignment === asignacionElegida.value &&
        a.unit === unidadElegida.value &&
        a.is_active !== false,
    );
  } catch {
    error.value = "No se pudieron cargar las actividades de la unidad. Probá de nuevo.";
  } finally {
    cargandoActividades.value = false;
  }
}

function abrirNueva(): void {
  formulario.name = "";
  formulario.activity_type = opcionesTipo.value[0]?.valor ?? "";
  formulario.max_score = "";
  formulario.due_date = "";
  modalAbierto.value = true;
}

async function guardar(): Promise<void> {
  guardando.value = true;
  error.value = "";
  try {
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
  } catch {
    error.value = "No se pudo guardar la actividad. Revisá los datos e intentá de nuevo.";
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

      <p v-if="cargandoUnidades || cargandoActividades">Cargando…</p>

      <template v-else-if="unidadElegida">
        <div class="unidad-page__resumen">
          <p>
            <strong>{{ puntosUsados }}</strong> de 100 puntos usados
            ({{ puntosDisponibles }} disponibles).
          </p>
          <p :class="{ 'unidad-page__aviso': cantidadPruebasCortas < 4 }">
            {{ cantidadPruebasCortas }} de 4 pruebas cortas como mínimo (RN-04).
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
        />
        <p v-else class="unidad-page__vacio">Todavía no hay actividades en esta unidad.</p>
      </template>

      <AppModal v-if="modalAbierto" titulo="Agregar actividad" @cerrar="modalAbierto = false">
        <form class="unidad-page__formulario" @submit.prevent="guardar">
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
            :pista="`Quedan ${puntosDisponibles} puntos disponibles en esta unidad.`"
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
  display: flex;
  gap: var(--espacio-xl);
  margin-bottom: var(--espacio-xl);
  flex-wrap: wrap;
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

.unidad-page__formulario {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-lg);
}
</style>
