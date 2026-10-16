<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";

import { conductReportsApi } from "@/features/comunicacion/api/comunicacionApi";
import { usePortalStore } from "@/features/portal/stores/portalStore";
import { CargandoBloque, EmptyState, ErrorBanner, PageHeader } from "@/shared/components";
import type { Attendance, ConductReport } from "@/shared/types/models";

import { attendanceApi } from "../api/portalApi";
import AsistenciaCalendario from "./AsistenciaCalendario.vue";
import ReportesConductaFamilia from "./ReportesConductaFamilia.vue";


const portal = usePortalStore();

const cargando = ref(true);
const error = ref("");
const asistencias = ref<Attendance[]>([]);
const reportes = ref<ConductReport[]>([]);

const inscripcionesIds = computed(
  () => new Set(portal.inscripcionesDelSeleccionado.map((i) => i.public_id)),
);

interface Grupo {
  etiqueta: string;
  registros: Attendance[];
}

const grupos = computed<Grupo[]>(() => {
  const propias = asistencias.value
    .filter((a) => inscripcionesIds.value.has(a.enrollment))
    .sort((a, b) => b.date.localeCompare(a.date));
  const matutina = propias.filter((a) => a.section_type === "academica");
  const taller = propias.filter((a) => a.section_type === "taller");
  const grupos: Grupo[] = [];
  if (matutina.length > 0) grupos.push({ etiqueta: "Jornada matutina", registros: matutina });
  if (taller.length > 0) grupos.push({ etiqueta: "Taller", registros: taller });
  return grupos;
});

const reportesPropios = computed(() =>
  reportes.value
    .filter((r) => inscripcionesIds.value.has(r.enrollment))
    .sort((a, b) => b.report_date.localeCompare(a.report_date)),
);

async function cargar(): Promise<void> {
  if (!portal.estudianteSeleccionadoId) return;
  cargando.value = true;
  error.value = "";
  try {
    const [asistenciasResp, reportesResp] = await Promise.all([
      attendanceApi.listar(),
      conductReportsApi.listar(),
    ]);
    asistencias.value = asistenciasResp.results;
    reportes.value = reportesResp.results;
  } catch {
    error.value = "No se pudo cargar la asistencia. Inténtalo de nuevo.";
  } finally {
    cargando.value = false;
  }
}

watch(() => portal.estudianteSeleccionadoId, cargar);
onMounted(cargar);
</script>

<template>
  <section class="asistencia-page">
    <PageHeader titulo="Asistencia" />

    <ErrorBanner v-if="error" :mensaje="error" etiqueta-accion="Reintentar" @accion="cargar" />
    <CargandoBloque v-else-if="cargando" />

    <template v-else>
      <EmptyState
        v-if="grupos.length === 0"
        titulo="Todavía no hay asistencia registrada"
        descripcion="Los registros de asistencia van a aparecer aquí."
      />
      <div v-for="grupo in grupos" :key="grupo.etiqueta" class="asistencia-page__grupo">
        <h2>{{ grupo.etiqueta }}</h2>
        <AsistenciaCalendario :registros="grupo.registros" />
      </div>

      <h2>Reportes de conducta</h2>
      <ReportesConductaFamilia :reportes="reportesPropios" />
    </template>
  </section>
</template>

<style scoped>

.asistencia-page h2 {
  font-family: var(--fuente-titulo);
  font-size: var(--texto-base);
  margin: var(--espacio-xl) 0 var(--espacio-sm);
}


</style>
