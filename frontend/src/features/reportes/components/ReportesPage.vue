<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";

import { ciclosApi, seccionesApi, unidadesApi } from "@/features/catalogo/api/catalogoApi";
import { AppButton, CargandoBloque, DataTable, EmptyState, ErrorBanner, FormSelect, PageHeader } from "@/shared/components";
import type { GradingUnit, SchoolCycle, Section } from "@/shared/types/models";

import { REPORTES, consultarReporte, descargarReportePdf } from "../api/reportesApi";
import type { FilaReporte } from "../api/reportesApi";
import { descargarArchivo } from "@/features/pagos/api/pagosApi";

const cargandoBase = ref(true);
const error = ref("");
const ciclos = ref<SchoolCycle[]>([]);
const secciones = ref<Section[]>([]);
const unidades = ref<GradingUnit[]>([]);

const rutaElegida = ref(REPORTES[0].ruta);
const reporte = computed(() => REPORTES.find((r) => r.ruta === rutaElegida.value)!);

const filtros = reactive({ cycle: "", section: "", unit: "" });

const opcionesReporte = REPORTES.map((r) => ({ valor: r.ruta, etiqueta: r.titulo }));
const opcionesCiclo = computed(() => ciclos.value.map((c) => ({ valor: c.public_id, etiqueta: String(c.year) })));
const opcionesSeccion = computed(() =>
  secciones.value.map((s) => ({ valor: s.public_id, etiqueta: `${s.grade} ${s.letter ?? ""}`.trimEnd() })),
);
const opcionesUnidad = computed(() => unidades.value.map((u) => ({ valor: u.public_id, etiqueta: `Unidad ${u.number}` })));

const cargandoFilas = ref(false);
const filas = ref<FilaReporte[]>([]);
const descargando = ref(false);

function paramsActivos(): Record<string, string> {
  const params: Record<string, string> = {};
  for (const filtro of reporte.value.filtros) {
    if (filtros[filtro]) params[filtro] = filtros[filtro];
  }
  return params;
}

async function cargarBase(): Promise<void> {
  cargandoBase.value = true;
  error.value = "";
  try {
    const [ciclosResp, seccionesResp] = await Promise.all([ciclosApi.listar(), seccionesApi.listar()]);
    ciclos.value = ciclosResp.results;
    secciones.value = seccionesResp.results;
  } catch {
    error.value = "No se pudo cargar la información inicial. Probá de nuevo.";
  } finally {
    cargandoBase.value = false;
  }
}

async function cargarUnidades(): Promise<void> {
  if (!filtros.cycle) {
    unidades.value = [];
    return;
  }
  unidades.value = (await unidadesApi(filtros.cycle).listar()).results;
}

async function consultar(): Promise<void> {
  cargandoFilas.value = true;
  error.value = "";
  try {
    filas.value = await consultarReporte(rutaElegida.value, paramsActivos());
  } catch {
    error.value = "No se pudo consultar el reporte. Probá de nuevo.";
  } finally {
    cargandoFilas.value = false;
  }
}

async function descargar(): Promise<void> {
  descargando.value = true;
  error.value = "";
  try {
    const { blob, nombreArchivo } = await descargarReportePdf(rutaElegida.value, paramsActivos());
    descargarArchivo(blob, nombreArchivo);
  } catch {
    error.value = "No se pudo generar el PDF. Probá de nuevo.";
  } finally {
    descargando.value = false;
  }
}

watch(rutaElegida, () => {
  filtros.cycle = "";
  filtros.section = "";
  filtros.unit = "";
  filas.value = [];
});
watch(() => filtros.cycle, cargarUnidades);

onMounted(async () => {
  await cargarBase();
  await consultar();
});
</script>

<template>
  <section class="reportes-page">
    <PageHeader titulo="Reportes institucionales" />

    <ErrorBanner v-if="error" :mensaje="error" etiqueta-accion="Reintentar" @accion="consultar" />
    <CargandoBloque v-else-if="cargandoBase" />

    <template v-else>
      <div class="reportes-page__filtros">
        <FormSelect id="reporte" etiqueta="Reporte" :opciones="opcionesReporte" v-model="rutaElegida" />
        <FormSelect
          v-if="reporte.filtros.includes('cycle')"
          id="cycle"
          etiqueta="Ciclo (opcional)"
          :opciones="opcionesCiclo"
          v-model="filtros.cycle"
        />
        <FormSelect
          v-if="reporte.filtros.includes('section')"
          id="section"
          etiqueta="Sección (opcional)"
          :opciones="opcionesSeccion"
          v-model="filtros.section"
        />
        <FormSelect
          v-if="reporte.filtros.includes('unit')"
          id="unit"
          etiqueta="Unidad (opcional)"
          :opciones="opcionesUnidad"
          v-model="filtros.unit"
        />
      </div>

      <div class="reportes-page__acciones">
        <AppButton :deshabilitado="cargandoFilas" @click="consultar">
          {{ cargandoFilas ? "Consultando…" : "Consultar" }}
        </AppButton>
        <AppButton variante="secundario" :deshabilitado="descargando" @click="descargar">
          {{ descargando ? "Generando…" : "Descargar PDF" }}
        </AppButton>
      </div>

      <CargandoBloque v-if="cargandoFilas" />
      <EmptyState
        v-else-if="filas.length === 0"
        titulo="Sin resultados"
        descripcion="No hay registros para los filtros elegidos."
      />
      <DataTable v-else class="reportes-page__tabla" :columnas="reporte.columnas" :filas="filas" />
    </template>
  </section>
</template>

<style scoped>

.reportes-page__filtros {
  display: flex;
  gap: var(--espacio-xl);
  flex-wrap: wrap;
  margin-bottom: var(--espacio-lg);
}

.reportes-page__acciones {
  display: flex;
  gap: var(--espacio-md);
  margin-bottom: var(--espacio-lg);
}

.reportes-page__tabla {
  overflow-x: auto;
  display: block;
}
</style>
