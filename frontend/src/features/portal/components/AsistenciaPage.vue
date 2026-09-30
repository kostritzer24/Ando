<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";

import { conductReportsApi } from "@/features/comunicacion/api/comunicacionApi";
import { usePortalStore } from "@/features/portal/stores/portalStore";
import { CargandoBloque, EmptyState, ErrorBanner, PageHeader, TagPill } from "@/shared/components";
import type { Attendance, ConductReport } from "@/shared/types/models";

import { attendanceApi } from "../api/portalApi";

const ETIQUETA_ESTADO: Record<string, string> = {
  presente: "Presente",
  tarde: "Tarde",
  ausente: "Ausente",
  justificado: "Justificado",
};
const VARIANTE_ESTADO: Record<string, "taller" | "aviso" | "alerta"> = {
  presente: "taller",
  tarde: "aviso",
  ausente: "alerta",
  justificado: "aviso",
};
const ETIQUETA_GRAVEDAD: Record<string, string> = {
  leve: "Leve",
  grave: "Grave",
  muy_grave: "Muy grave",
};

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
    error.value = "No se pudo cargar la asistencia. Probá de nuevo.";
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
        descripcion="Los registros de asistencia van a aparecer acá."
      />
      <div v-for="grupo in grupos" :key="grupo.etiqueta" class="asistencia-page__grupo">
        <h2>{{ grupo.etiqueta }}</h2>
        <ul class="asistencia-page__lista">
          <li v-for="registro in grupo.registros" :key="registro.public_id" class="asistencia-page__fila">
            <span>{{ registro.date }}</span>
            <TagPill :variante="VARIANTE_ESTADO[registro.status]">
              {{ ETIQUETA_ESTADO[registro.status] }}
            </TagPill>
          </li>
        </ul>
      </div>

      <h2>Reportes de conducta</h2>
      <EmptyState
        v-if="reportesPropios.length === 0"
        titulo="No hay reportes de conducta"
        descripcion="Los reportes de conducta registrados van a aparecer acá."
      />
      <ul v-else class="asistencia-page__reportes">
        <li v-for="reporte in reportesPropios" :key="reporte.public_id" class="asistencia-page__reporte">
          <p class="asistencia-page__reporte-fecha">{{ reporte.report_date }} — {{ ETIQUETA_GRAVEDAD[reporte.severity] }}</p>
          <p>{{ reporte.incident_description }}</p>
        </li>
      </ul>
    </template>
  </section>
</template>

<style scoped>

.asistencia-page h2 {
  font-family: var(--fuente-titulo);
  font-size: var(--texto-base);
  margin: var(--espacio-xl) 0 var(--espacio-sm);
}

.asistencia-page__lista {
  list-style: none;
  margin: 0;
  padding: 0;
}

.asistencia-page__fila {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--espacio-sm) 0;
  border-bottom: 1px solid var(--color-linea);
}

.asistencia-page__reportes {
  list-style: none;
  margin: 0;
  padding: 0;
}

.asistencia-page__reporte {
  padding: var(--espacio-sm) 0;
  border-bottom: 1px solid var(--color-linea);
}

.asistencia-page__reporte-fecha {
  margin: 0;
  font-weight: 600;
}
</style>
