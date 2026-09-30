<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";

import { unidadesApi } from "@/features/catalogo/api/catalogoApi";
import { descargarArchivo } from "@/features/pagos/api/pagosApi";
import { usePortalStore } from "@/features/portal/stores/portalStore";
import { AppButton, CargandoBloque, EmptyState, ErrorBanner, PageHeader } from "@/shared/components";
import type { Grade, GradingUnit, ReportCard } from "@/shared/types/models";

import { descargarBoletin, gradesApi, reportCardsApi } from "../api/portalApi";

const portal = usePortalStore();

const cargando = ref(true);
const error = ref("");
const notas = ref<Grade[]>([]);
const boletines = ref<ReportCard[]>([]);
const unidades = ref<GradingUnit[]>([]);
const descargandoId = ref("");
const errorDescarga = ref("");

function numeroDeUnidad(unitPublicId: string): number | undefined {
  return unidades.value.find((u) => u.public_id === unitPublicId)?.number;
}

const inscripcionesIds = computed(
  () => new Set(portal.inscripcionesDelSeleccionado.map((i) => i.public_id)),
);

interface FilaUnidad {
  unidad: number;
  nota: number;
  actividades: { nombre: string; nota: number; maximo: number }[];
}
interface GrupoCurso {
  curso: string;
  unidades: FilaUnidad[];
}

const notasPorCurso = computed<GrupoCurso[]>(() => {
  const propias = notas.value.filter((n) => inscripcionesIds.value.has(n.enrollment));
  const cursos = new Map<string, Map<number, FilaUnidad>>();
  for (const nota of propias) {
    const courseName = nota.course_name;
    const unitNumber = nota.unit_number;
    const activityName = nota.activity_name;
    const maxScore = Number(nota.max_score);
    if (!cursos.has(courseName)) cursos.set(courseName, new Map());
    const unidades = cursos.get(courseName)!;
    if (!unidades.has(unitNumber)) unidades.set(unitNumber, { unidad: unitNumber, nota: 0, actividades: [] });
    const fila = unidades.get(unitNumber)!;
    fila.nota += Number(nota.current_score);
    fila.actividades.push({ nombre: activityName, nota: Number(nota.current_score), maximo: maxScore });
  }
  return Array.from(cursos.entries())
    .map(([curso, unidades]) => ({
      curso,
      unidades: Array.from(unidades.values()).sort((a, b) => a.unidad - b.unidad),
    }))
    .sort((a, b) => a.curso.localeCompare(b.curso));
});

const boletinesPropios = computed(() =>
  boletines.value
    .filter((b) => inscripcionesIds.value.has(b.enrollment))
    .sort((a, b) => a.unit.localeCompare(b.unit)),
);

async function cargar(): Promise<void> {
  if (!portal.estudianteSeleccionadoId) return;
  cargando.value = true;
  error.value = "";
  try {
    const [notasResp, boletinesResp] = await Promise.all([gradesApi.listar(), reportCardsApi.listar()]);
    notas.value = notasResp.results;
    boletines.value = boletinesResp.results;
    const cicloId = portal.inscripcionesDelSeleccionado[0]?.cycle;
    unidades.value = cicloId ? (await unidadesApi(cicloId).listar()).results : [];
  } catch {
    error.value = "No se pudieron cargar las notas. Probá de nuevo.";
  } finally {
    cargando.value = false;
  }
}

async function descargar(boletin: ReportCard): Promise<void> {
  descargandoId.value = boletin.public_id;
  errorDescarga.value = "";
  try {
    const { blob, nombreArchivo } = await descargarBoletin(boletin.public_id);
    descargarArchivo(blob, nombreArchivo);
  } catch {
    errorDescarga.value = "No se pudo descargar el boletín. Probá de nuevo.";
  } finally {
    descargandoId.value = "";
  }
}

watch(() => portal.estudianteSeleccionadoId, cargar);
onMounted(cargar);
</script>

<template>
  <section class="notas-page">
    <PageHeader titulo="Notas" />

    <ErrorBanner v-if="error" :mensaje="error" etiqueta-accion="Reintentar" @accion="cargar" />
    <CargandoBloque v-else-if="cargando" />

    <template v-else>
      <EmptyState
        v-if="notasPorCurso.length === 0"
        titulo="Todavía no hay notas"
        descripcion="Las notas registradas por los docentes van a aparecer acá, por curso y por unidad."
      />
      <div v-else class="notas-page__cursos">
        <article v-for="grupo in notasPorCurso" :key="grupo.curso" class="notas-page__curso">
          <h2>{{ grupo.curso }}</h2>
          <div v-for="fila in grupo.unidades" :key="fila.unidad" class="notas-page__unidad">
            <p class="notas-page__unidad-titulo">Unidad {{ fila.unidad }} — {{ fila.nota }} / 100</p>
            <ul class="notas-page__actividades">
              <li v-for="(act, indice) in fila.actividades" :key="indice">
                {{ act.nombre }}: {{ act.nota }} / {{ act.maximo }}
              </li>
            </ul>
          </div>
        </article>
      </div>

      <h2>Boletines</h2>
      <ErrorBanner v-if="errorDescarga" :mensaje="errorDescarga" />
      <EmptyState
        v-if="boletinesPropios.length === 0"
        titulo="Todavía no hay boletines publicados"
        descripcion="Cuando Dirección publique un boletín, va a aparecer acá para descargar."
      />
      <ul v-else class="notas-page__boletines">
        <li v-for="boletin in boletinesPropios" :key="boletin.public_id" class="notas-page__boletin">
          <span>Boletín — Unidad {{ numeroDeUnidad(boletin.unit) ?? "" }}</span>
          <AppButton
            variante="secundario"
            :deshabilitado="descargandoId === boletin.public_id"
            @click="descargar(boletin)"
          >
            {{ descargandoId === boletin.public_id ? "Generando…" : "Descargar" }}
          </AppButton>
        </li>
      </ul>
    </template>
  </section>
</template>

<style scoped>

.notas-page h2 {
  font-family: var(--fuente-titulo);
  font-size: var(--texto-base);
  margin: var(--espacio-xl) 0 var(--espacio-md);
}

.notas-page__curso {
  margin-bottom: var(--espacio-lg);
}

.notas-page__curso h2 {
  font-size: var(--texto-base);
  margin: 0 0 var(--espacio-sm);
}

.notas-page__unidad {
  margin-bottom: var(--espacio-sm);
}

.notas-page__unidad-titulo {
  margin: 0;
  font-weight: 600;
}

.notas-page__actividades {
  margin: var(--espacio-2xs) 0 0;
  padding-left: 1.2rem;
  color: var(--color-tinta-suave);
  font-size: var(--texto-sm);
}

.notas-page__boletines {
  list-style: none;
  margin: 0;
  padding: 0;
}

.notas-page__boletin {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--espacio-sm) 0;
  border-bottom: 1px solid var(--color-linea);
}
</style>
