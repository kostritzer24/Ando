<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { CargandoBloque, EmptyState, ErrorBanner, PageHeader } from "@/shared/components";

import { type BloqueHorarioPropio, DIAS, filasDePeriodos, type Jornada, obtenerMiHorario } from "../api/horariosApi";

const cargando = ref(true);
const error = ref("");
const bloques = ref<BloqueHorarioPropio[]>([]);

function bloqueEn(dia: string, periodo: number): BloqueHorarioPropio | undefined {
  return bloques.value.find((b) => b.day_of_week === dia && b.period_number === periodo);
}

const filas = computed(() => {
  const jornadas = [...new Set(bloques.value.map((b) => b.jornada))] as Jornada[];
  const hayTaller = bloques.value.some((b) => b.period_number >= 7);
  const hayJornada = bloques.value.some((b) => b.period_number < 7);
  return filasDePeriodos(jornadas, { jornada: hayJornada || !hayTaller, taller: hayTaller });
});

async function cargar(): Promise<void> {
  cargando.value = true;
  error.value = "";
  try {
    bloques.value = await obtenerMiHorario();
  } catch {
    error.value = "No se pudo cargar tu horario. Inténtalo de nuevo.";
  } finally {
    cargando.value = false;
  }
}

onMounted(cargar);
</script>

<template>
  <section class="mi-horario">
    <PageHeader titulo="Mi horario" />

    <ErrorBanner v-if="error" :mensaje="error" etiqueta-accion="Reintentar" @accion="cargar" />
    <CargandoBloque v-else-if="cargando" />
    <EmptyState
      v-else-if="bloques.length === 0"
      titulo="Todavía no tienes horario asignado"
      descripcion="Dirección arma el horario del centro; cuando te asigne clases, van a aparecer aquí."
    />

    <table v-else class="mi-horario__tabla">
      <thead>
        <tr>
          <th></th>
          <th v-for="dia in DIAS" :key="dia.valor">{{ dia.etiqueta }}</th>
        </tr>
      </thead>
      <tbody>
        <template v-for="periodo in filas" :key="periodo.numero">
        <tr v-for="receso in periodo.recesos" :key="receso" class="mi-horario__receso">
          <td :colspan="DIAS.length + 1">{{ receso }}</td>
        </tr>
        <tr>
          <th class="mi-horario__hora">P{{ periodo.numero }}<br /><small>{{ periodo.horario }}</small></th>
          <td v-for="dia in DIAS" :key="dia.valor">
            <div v-if="bloqueEn(dia.valor, periodo.numero)" class="mi-horario__celda">
              <strong>{{ bloqueEn(dia.valor, periodo.numero)!.course }}</strong>
              <span>{{ bloqueEn(dia.valor, periodo.numero)!.section }}</span>
            </div>
          </td>
        </tr>
        </template>
      </tbody>
    </table>
  </section>
</template>

<style scoped>

.mi-horario__tabla {
  border-collapse: collapse;
  width: 100%;
}

.mi-horario__tabla th,
.mi-horario__tabla td {
  border: 1px solid var(--color-linea);
  padding: var(--espacio-xs);
  text-align: center;
  font-size: var(--texto-sm);
}

.mi-horario__hora {
  white-space: nowrap;
  color: var(--color-tinta-suave);
  font-weight: 600;
}

.mi-horario__receso td {
  padding: var(--espacio-2xs);
  background: var(--color-etiqueta-aviso-fondo);
  color: var(--color-etiqueta-aviso-texto);
  font-size: var(--texto-xs);
  text-transform: uppercase;
}

.mi-horario__celda {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}
</style>
