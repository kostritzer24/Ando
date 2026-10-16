<script setup lang="ts">
import type { HorarioEnCuadricula } from "@/features/reportes/api/reportesApi";

/** Horario de solo lectura: una fila por período, una columna por día. */
defineProps<{ horario: HorarioEnCuadricula }>();
</script>

<template>
  <div class="horario-cuadricula">
    <div class="horario-cuadricula__marco">
      <table class="horario-cuadricula__tabla">
        <caption class="horario-cuadricula__titulo">
          {{ horario.titulo }}
          <small>{{ horario.subtitulo }}</small>
        </caption>
        <thead>
          <tr>
            <th scope="col">Período</th>
            <th v-for="dia in horario.dias" :key="dia.clave" scope="col">{{ dia.etiqueta }}</th>
          </tr>
        </thead>
        <tbody>
          <template v-for="periodo in horario.periodos" :key="periodo.numero">
            <tr v-if="periodo.receso_antes" class="horario-cuadricula__receso">
              <td :colspan="horario.dias.length + 1">Receso {{ horario.receso.inicio }}–{{ horario.receso.fin }}</td>
            </tr>
            <tr>
              <th scope="row" class="horario-cuadricula__hora">
                P{{ periodo.numero }}<small>{{ periodo.inicio }}–{{ periodo.fin }}</small>
              </th>
              <td v-for="dia in horario.dias" :key="dia.clave">
                <div v-if="periodo.celdas[dia.clave]" class="horario-cuadricula__clase">
                  <strong>{{ periodo.celdas[dia.clave]!.curso }}</strong>
                  <span>{{ periodo.celdas[dia.clave]!.detalle }}</span>
                </div>
                <span v-else class="horario-cuadricula__libre" aria-label="Libre">—</span>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.horario-cuadricula__marco {
  overflow-x: auto;
  background: var(--color-papel);
  border: 1px solid var(--color-linea);
  border-radius: var(--radio-lg);
}

.horario-cuadricula__tabla {
  border-collapse: collapse;
  width: 100%;
  min-width: 40rem;
  table-layout: fixed;
}

.horario-cuadricula__titulo {
  padding: var(--espacio-md);
  text-align: left;
  font-family: var(--fuente-titulo);
  font-weight: 700;
}

.horario-cuadricula__titulo small {
  display: block;
  font-family: var(--fuente-cuerpo);
  font-weight: 400;
  color: var(--color-tinta-suave);
}

.horario-cuadricula__tabla th,
.horario-cuadricula__tabla td {
  padding: var(--espacio-xs);
  border-top: 1px solid var(--color-linea);
  border-right: 1px solid var(--color-linea);
  text-align: center;
  vertical-align: middle;
  font-size: var(--texto-sm);
}

.horario-cuadricula__tabla tr > :last-child {
  border-right: none;
}

.horario-cuadricula__tabla thead th {
  color: var(--color-tinta-suave);
  font-weight: 600;
}

.horario-cuadricula__tabla th:first-child {
  width: 6.5rem;
}

.horario-cuadricula__hora small {
  display: block;
  font-weight: 400;
  color: var(--color-tinta-suave);
  font-variant-numeric: tabular-nums;
}

.horario-cuadricula__clase {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
  padding: var(--espacio-xs) var(--espacio-sm);
  background: var(--color-etiqueta-hoy-fondo);
  color: var(--color-etiqueta-hoy-texto);
  border-radius: var(--radio-sm);
  text-align: left;
  overflow-wrap: anywhere;
}

.horario-cuadricula__clase span {
  font-size: var(--texto-xs);
}

.horario-cuadricula__libre {
  color: var(--color-linea-fuerte);
}

.horario-cuadricula__tabla tr.horario-cuadricula__receso > td {
  padding: var(--espacio-2xs);
  background: var(--color-etiqueta-aviso-fondo);
  color: var(--color-etiqueta-aviso-texto);
  font-size: var(--texto-xs);
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
</style>
