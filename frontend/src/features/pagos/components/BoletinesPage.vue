<script setup lang="ts">
import { isAxiosError } from "axios";
import { computed, onMounted, ref, watch } from "vue";

import { seccionesApi, unidadesApi } from "@/features/catalogo/api/catalogoApi";
import { enrollmentsApi, studentsApi } from "@/features/estudiantes/api/estudiantesApi";
import { AppButton, CargandoBloque, DataTable, EmptyState, ErrorBanner, FormSelect, PageHeader, TagPill } from "@/shared/components";
import { usePermisos } from "@/shared/permisos";
import type { Enrollment, GradingUnit, ReportCard, Section, Student } from "@/shared/types/models";

import { aprobarBoletin, generarBoletines, publicarBoletin, reportCardsApi } from "../api/pagosApi";

// Generar, aprobar y publicar es "editar" en Notas (Dirección);
// Coordinación y Administrador los consultan.
const permisos = usePermisos();
const puedeGestionar = computed(() => permisos.puedeEditar("notas"));

const ETIQUETA_ESTADO: Record<string, string> = {
  borrador: "Borrador",
  aprobado: "Aprobado",
  publicado: "Publicado",
};
const VARIANTE_ESTADO: Record<string, "hoy" | "aviso" | "taller"> = {
  borrador: "hoy",
  aprobado: "aviso",
  publicado: "taller",
};

const cargando = ref(true);
const error = ref("");
const secciones = ref<Section[]>([]);
const inscripciones = ref<Enrollment[]>([]);
const estudiantes = ref<Student[]>([]);

const seccionElegida = ref("");
const unidades = ref<GradingUnit[]>([]);
const unidadElegida = ref("");
const cargandoUnidades = ref(false);

const boletines = ref<ReportCard[]>([]);
const cargandoBoletines = ref(false);
const generando = ref(false);
const errorAccion = ref("");
const idEnAccion = ref("");

const opcionesSeccion = computed(() =>
  secciones.value.map((s) => ({ valor: s.public_id, etiqueta: `${s.grade} ${s.letter ?? ""}`.trimEnd() })),
);
const opcionesUnidad = computed(() =>
  unidades.value.map((u) => ({ valor: u.public_id, etiqueta: `Unidad ${u.number}` })),
);

function nombreEstudiante(enrollmentPublicId: string): string {
  const inscripcion = inscripciones.value.find((i) => i.public_id === enrollmentPublicId);
  const estudiante = inscripcion ? estudiantes.value.find((e) => e.public_id === inscripcion.student) : undefined;
  return estudiante ? `${estudiante.first_name} ${estudiante.last_name}` : "—";
}

async function cargar(): Promise<void> {
  cargando.value = true;
  error.value = "";
  try {
    const [seccionesResp, inscripcionesResp, estudiantesResp] = await Promise.all([
      seccionesApi.listar(),
      enrollmentsApi.listar(),
      studentsApi.listar(),
    ]);
    secciones.value = seccionesResp.results.filter((s) => s.is_active !== false);
    inscripciones.value = inscripcionesResp.results;
    estudiantes.value = estudiantesResp.results;
    seccionElegida.value = opcionesSeccion.value[0]?.valor ?? "";
  } catch {
    error.value = "No se pudo cargar la lista de secciones. Probá de nuevo.";
  } finally {
    cargando.value = false;
  }
}

async function cargarUnidades(): Promise<void> {
  const seccion = secciones.value.find((s) => s.public_id === seccionElegida.value);
  if (!seccion) {
    unidades.value = [];
    return;
  }
  cargandoUnidades.value = true;
  try {
    unidades.value = (await unidadesApi(seccion.cycle).listar()).results;
    unidadElegida.value = opcionesUnidad.value[0]?.valor ?? "";
  } catch {
    error.value = "No se pudieron cargar las unidades de este ciclo. Probá de nuevo.";
  } finally {
    cargandoUnidades.value = false;
  }
}

async function cargarBoletines(): Promise<void> {
  if (!seccionElegida.value || !unidadElegida.value) {
    boletines.value = [];
    return;
  }
  cargandoBoletines.value = true;
  error.value = "";
  try {
    const inscripcionesDeLaSeccion = new Set(
      inscripciones.value.filter((i) => i.section === seccionElegida.value).map((i) => i.public_id),
    );
    const todos = (await reportCardsApi.listar()).results;
    boletines.value = todos.filter(
      (b) => b.unit === unidadElegida.value && inscripcionesDeLaSeccion.has(b.enrollment),
    );
  } catch {
    error.value = "No se pudieron cargar los boletines de esta sección. Probá de nuevo.";
  } finally {
    cargandoBoletines.value = false;
  }
}

async function generar(): Promise<void> {
  generando.value = true;
  errorAccion.value = "";
  try {
    await generarBoletines({ section: seccionElegida.value, unit: unidadElegida.value });
    await cargarBoletines();
  } catch {
    errorAccion.value = "No se pudieron generar los boletines. Probá de nuevo.";
  } finally {
    generando.value = false;
  }
}

function mensajeDeError(error: unknown, porOmision: string): string {
  if (isAxiosError(error) && Array.isArray(error.response?.data)) {
    return String(error.response.data[0]);
  }
  return porOmision;
}

async function aprobar(boletin: ReportCard): Promise<void> {
  idEnAccion.value = boletin.public_id;
  errorAccion.value = "";
  try {
    await aprobarBoletin(boletin.public_id);
    await cargarBoletines();
  } catch (error) {
    errorAccion.value = mensajeDeError(error, "No se pudo aprobar el boletín.");
  } finally {
    idEnAccion.value = "";
  }
}

async function publicar(boletin: ReportCard): Promise<void> {
  idEnAccion.value = boletin.public_id;
  errorAccion.value = "";
  try {
    await publicarBoletin(boletin.public_id);
    await cargarBoletines();
  } catch (error) {
    errorAccion.value = mensajeDeError(error, "No se pudo publicar el boletín.");
  } finally {
    idEnAccion.value = "";
  }
}

watch(seccionElegida, cargarUnidades);
watch([seccionElegida, unidadElegida], cargarBoletines);

onMounted(async () => {
  await cargar();
  await cargarUnidades();
});
</script>

<template>
  <section class="boletines-page">
    <PageHeader titulo="Boletines" />

    <ErrorBanner v-if="error" :mensaje="error" etiqueta-accion="Reintentar" @accion="cargar" />
    <CargandoBloque v-else-if="cargando" />

    <template v-else>
      <div class="boletines-page__filtros">
        <FormSelect id="section" etiqueta="Sección" :opciones="opcionesSeccion" v-model="seccionElegida" />
        <FormSelect id="unit" etiqueta="Unidad" :opciones="opcionesUnidad" v-model="unidadElegida" />
      </div>

      <CargandoBloque v-if="cargandoUnidades || cargandoBoletines" />

      <template v-else-if="unidadElegida">
        <div v-if="puedeGestionar" class="boletines-page__barra">
          <AppButton variante="secundario" :deshabilitado="generando" @click="generar">
            {{ generando ? "Generando…" : "Generar boletines" }}
          </AppButton>
        </div>

        <ErrorBanner v-if="errorAccion" :mensaje="errorAccion" />

        <EmptyState
          v-if="boletines.length === 0"
          titulo="No hay boletines"
          :descripcion="puedeGestionar ? 'Generá los boletines de esta sección y unidad para empezar.' : 'Todavía no se generaron los boletines de esta sección y unidad.'"
        />

        <DataTable
          v-else
          class="boletines-page__tabla"
          :columnas="[
            { clave: 'estudiante', etiqueta: 'Estudiante' },
            { clave: 'estado', etiqueta: 'Estado' },
          ]"
          :filas="boletines.map((b) => ({ ...b, estudiante: nombreEstudiante(b.enrollment) }))"
        >
          <template #celda-estado="{ fila }">
            <TagPill :variante="VARIANTE_ESTADO[(fila as unknown as ReportCard).status]">
              {{ ETIQUETA_ESTADO[(fila as unknown as ReportCard).status] }}
            </TagPill>
          </template>
          <template v-if="puedeGestionar" #acciones="{ fila }">
            <button
              v-if="(fila as unknown as ReportCard).status === 'borrador'"
              type="button"
              class="boletines-page__accion"
              :disabled="idEnAccion === (fila as unknown as ReportCard).public_id"
              @click="aprobar(fila as unknown as ReportCard)"
            >
              Aprobar
            </button>
            <button
              v-else-if="(fila as unknown as ReportCard).status === 'aprobado'"
              type="button"
              class="boletines-page__accion"
              :disabled="idEnAccion === (fila as unknown as ReportCard).public_id"
              @click="publicar(fila as unknown as ReportCard)"
            >
              Publicar
            </button>
          </template>
        </DataTable>
      </template>
    </template>
  </section>
</template>

<style scoped>

.boletines-page__filtros {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 13rem), 1fr));
  gap: var(--espacio-md) var(--espacio-lg);
  align-items: end;
  max-width: 52rem;
}

.boletines-page__tabla {
  margin-top: var(--espacio-lg);
}

.boletines-page__accion {
  background: none;
  border: none;
  color: var(--color-accion);
  font-size: var(--texto-sm);
  font-weight: 600;
  cursor: pointer;
  padding: 0.3rem 0.5rem;
}
</style>
