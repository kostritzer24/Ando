<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";

import { articulosConvivenciaApi } from "@/features/catalogo/api/catalogoApi";
import { enrollmentsApi, studentsApi } from "@/features/estudiantes/api/estudiantesApi";
import { AppButton, AppModal, DataTable, EmptyState, ErrorBanner, FormField, FormSelect } from "@/shared/components";
import type { ConductReport, ConductRuleArticle, Enrollment, Student } from "@/shared/types/models";

import { conductReportsApi, crearReporteConducta, descargarReporteConducta } from "../api/comunicacionApi";
import { descargarArchivo } from "@/features/pagos/api/pagosApi";

const GRAVEDADES = [
  { valor: "leve", etiqueta: "Leve" },
  { valor: "grave", etiqueta: "Grave" },
  { valor: "muy_grave", etiqueta: "Muy grave" },
];
const SANCIONES = [
  { valor: "llamado_verbal", etiqueta: "Llamado verbal" },
  { valor: "amonestacion_escrita", etiqueta: "Amonestación escrita" },
  { valor: "comunicacion_familia", etiqueta: "Comunicación a la familia" },
  { valor: "suspension_extracurricular", etiqueta: "Suspensión de actividades extracurriculares" },
  { valor: "servicio_comunitario", etiqueta: "Servicio comunitario" },
  { valor: "suspension_clases", etiqueta: "Suspensión de clases" },
  { valor: "evaluacion_expulsion", etiqueta: "Evaluación para expulsión" },
  { valor: "otra", etiqueta: "Otra" },
];

const cargando = ref(true);
const error = ref("");
const reportes = ref<ConductReport[]>([]);
const inscripciones = ref<Enrollment[]>([]);
const estudiantes = ref<Student[]>([]);
const articulos = ref<ConductRuleArticle[]>([]);
const descargandoId = ref("");

const opcionesInscripcion = computed(() =>
  inscripciones.value.map((i) => {
    const estudiante = estudiantes.value.find((e) => e.public_id === i.student);
    const nombre = estudiante ? `${estudiante.first_name} ${estudiante.last_name}` : "—";
    return { valor: i.public_id, etiqueta: `${nombre} — ${i.section_grade} ${i.section_letter ?? ""}`.trimEnd() };
  }),
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
    const [reportesResp, inscripcionesResp, estudiantesResp, articulosResp] = await Promise.all([
      conductReportsApi.listar(),
      enrollmentsApi.listar(),
      studentsApi.listar(),
      articulosConvivenciaApi.listar(),
    ]);
    reportes.value = reportesResp.results;
    inscripciones.value = inscripcionesResp.results.filter((i) => i.status === "activo");
    estudiantes.value = estudiantesResp.results;
    articulos.value = articulosResp.results;
  } catch {
    error.value = "No se pudo cargar la información. Probá de nuevo.";
  } finally {
    cargando.value = false;
  }
}

const modalAbierto = ref(false);
const guardando = ref(false);
const errorGuardado = ref("");
const formulario = reactive({
  enrollment: "",
  report_date: "",
  severity: "leve",
  incident_description: "",
  immediate_actions: "",
  other_violation_detail: "",
  sanction_type: "llamado_verbal",
  sanction_detail: "",
  commitments: "",
  article_ids: [] as string[],
});

function abrirNuevo(): void {
  formulario.enrollment = opcionesInscripcion.value[0]?.valor ?? "";
  formulario.report_date = "";
  formulario.severity = "leve";
  formulario.incident_description = "";
  formulario.immediate_actions = "";
  formulario.other_violation_detail = "";
  formulario.sanction_type = "llamado_verbal";
  formulario.sanction_detail = "";
  formulario.commitments = "";
  formulario.article_ids = [];
  errorGuardado.value = "";
  modalAbierto.value = true;
}

async function guardar(): Promise<void> {
  guardando.value = true;
  errorGuardado.value = "";
  try {
    await crearReporteConducta({
      enrollment: formulario.enrollment,
      report_date: formulario.report_date,
      severity: formulario.severity as ConductReport["severity"],
      incident_description: formulario.incident_description,
      immediate_actions: formulario.immediate_actions,
      other_violation_detail: formulario.other_violation_detail,
      sanction_type: formulario.sanction_type as ConductReport["sanction_type"],
      sanction_detail: formulario.sanction_detail,
      commitments: formulario.commitments,
      article_ids: formulario.article_ids,
    });
    modalAbierto.value = false;
    await cargar();
  } catch {
    errorGuardado.value = "No se pudo registrar el reporte. Revisá los datos e intentá de nuevo.";
  } finally {
    guardando.value = false;
  }
}

async function descargar(reporte: ConductReport): Promise<void> {
  descargandoId.value = reporte.public_id;
  try {
    const { blob, nombreArchivo } = await descargarReporteConducta(reporte.public_id);
    descargarArchivo(blob, nombreArchivo);
  } catch {
    error.value = "No se pudo descargar el reporte. Probá de nuevo.";
  } finally {
    descargandoId.value = "";
  }
}

onMounted(cargar);
</script>

<template>
  <section class="reportes-conducta-page">
    <h1>Reportes de conducta</h1>

    <ErrorBanner v-if="error" :mensaje="error" etiqueta-accion="Reintentar" @accion="cargar" />
    <p v-else-if="cargando">Cargando…</p>

    <template v-else>
      <AppButton :deshabilitado="opcionesInscripcion.length === 0" @click="abrirNuevo">
        Registrar reporte
      </AppButton>

      <EmptyState
        v-if="reportes.length === 0"
        titulo="No hay reportes"
        descripcion="Los reportes de conducta registrados van a aparecer acá."
      />
      <DataTable
        v-else
        class="reportes-conducta-page__tabla"
        :columnas="[
          { clave: 'estudiante', etiqueta: 'Estudiante' },
          { clave: 'report_date', etiqueta: 'Fecha' },
          { clave: 'severity', etiqueta: 'Tipo de falta' },
          { clave: 'sanction_type', etiqueta: 'Sanción' },
        ]"
        :filas="
          reportes.map((r) => ({
            ...r,
            estudiante: nombreEstudiante(r.enrollment),
            severity: GRAVEDADES.find((g) => g.valor === r.severity)?.etiqueta ?? r.severity,
            sanction_type: SANCIONES.find((s) => s.valor === r.sanction_type)?.etiqueta ?? r.sanction_type,
          }))
        "
      >
        <template #acciones="{ fila }">
          <button
            type="button"
            class="reportes-conducta-page__accion"
            :disabled="descargandoId === (fila as unknown as ConductReport).public_id"
            @click="descargar(fila as unknown as ConductReport)"
          >
            Descargar PDF
          </button>
        </template>
      </DataTable>
    </template>

    <AppModal v-if="modalAbierto" titulo="Registrar reporte de conducta" @cerrar="modalAbierto = false">
      <form class="reportes-conducta-page__formulario" @submit.prevent="guardar">
        <ErrorBanner v-if="errorGuardado" :mensaje="errorGuardado" />
        <FormSelect
          id="enrollment"
          etiqueta="Estudiante"
          :opciones="opcionesInscripcion"
          v-model="formulario.enrollment"
        />
        <FormField id="report_date" etiqueta="Fecha" tipo="date" v-model="formulario.report_date" />
        <FormSelect id="severity" etiqueta="Tipo de falta" :opciones="GRAVEDADES" v-model="formulario.severity" />

        <fieldset class="reportes-conducta-page__articulos">
          <legend>Artículos del código de convivencia incumplidos</legend>
          <label v-for="articulo in articulos" :key="articulo.public_id">
            <input type="checkbox" :value="articulo.public_id" v-model="formulario.article_ids" />
            {{ articulo.code }} — {{ articulo.description }}
          </label>
        </fieldset>
        <FormField
          id="other_violation_detail"
          etiqueta="Otra falta no especificada (opcional)"
          v-model="formulario.other_violation_detail"
        />

        <FormField id="incident_description" etiqueta="Hechos ocurridos" v-model="formulario.incident_description" />
        <FormField id="immediate_actions" etiqueta="Medidas inmediatas tomadas" v-model="formulario.immediate_actions" />
        <FormSelect id="sanction_type" etiqueta="Sanción" :opciones="SANCIONES" v-model="formulario.sanction_type" />
        <FormField id="sanction_detail" etiqueta="Detalle de la sanción (opcional)" v-model="formulario.sanction_detail" />
        <FormField id="commitments" etiqueta="Compromisos establecidos" v-model="formulario.commitments" />

        <AppButton tipo="submit" :deshabilitado="guardando">
          {{ guardando ? "Guardando…" : "Guardar" }}
        </AppButton>
      </form>
    </AppModal>
  </section>
</template>

<style scoped>
.reportes-conducta-page h1 {
  font-family: var(--fuente-titulo);
  font-size: var(--texto-md);
  margin: 0 0 var(--espacio-lg);
}

.reportes-conducta-page__tabla {
  margin-top: var(--espacio-lg);
}

.reportes-conducta-page__accion {
  background: none;
  border: none;
  color: var(--color-accion);
  font-size: var(--texto-sm);
  font-weight: 600;
  cursor: pointer;
  padding: 0.3rem 0.5rem;
}

.reportes-conducta-page__formulario {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-lg);
}

.reportes-conducta-page__articulos {
  border: 1px solid var(--color-linea);
  border-radius: var(--radio-md);
  padding: var(--espacio-md);
  display: flex;
  flex-direction: column;
  gap: var(--espacio-xs);
  max-height: 12rem;
  overflow-y: auto;
}

.reportes-conducta-page__articulos legend {
  font-weight: 600;
  padding: 0 0.3rem;
}

.reportes-conducta-page__articulos label {
  display: flex;
  align-items: baseline;
  gap: var(--espacio-xs);
  font-size: var(--texto-sm);
}
</style>
