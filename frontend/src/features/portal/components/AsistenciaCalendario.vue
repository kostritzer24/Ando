<script setup lang="ts">
import { ChevronLeft, ChevronRight } from "lucide-vue-next";
import { computed, ref, watch } from "vue";

import { aFechaIso } from "@/shared/fechas";
import type { Attendance } from "@/shared/types/models";

/** Asistencia de un mes en calendario (lunes a viernes): no crece sin fin
 * como una lista, y de un vistazo se ven las faltas del mes. */
const props = defineProps<{ registros: Attendance[] }>();

const ETIQUETA: Record<string, string> = {
  presente: "Presente",
  ausente: "Ausente",
  justificado: "Justificado",
};
const LETRA: Record<string, string> = { presente: "P", ausente: "A", justificado: "J" };
const DIAS_SEMANA = ["Lun", "Mar", "Mié", "Jue", "Vie"];
const MESES = [
  "enero", "febrero", "marzo", "abril", "mayo", "junio",
  "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
];

const porFecha = computed(() => new Map(props.registros.map((r) => [r.date, r.status])));

function mesInicial(): Date {
  const ultima = [...props.registros].sort((a, b) => b.date.localeCompare(a.date))[0]?.date;
  const base = ultima ? new Date(`${ultima}T12:00:00`) : new Date();
  return new Date(base.getFullYear(), base.getMonth(), 1);
}

const mes = ref(mesInicial());
watch(() => props.registros, () => (mes.value = mesInicial()));

const titulo = computed(() => `${MESES[mes.value.getMonth()]} ${mes.value.getFullYear()}`);

function cambiarMes(delta: number): void {
  mes.value = new Date(mes.value.getFullYear(), mes.value.getMonth() + delta, 1);
}

interface Celda {
  fecha: string;
  dia: number;
  estado?: string;
}

// Semanas de lunes a viernes; los sábados y domingos no se muestran.
const semanas = computed<(Celda | null)[][]>(() => {
  const anio = mes.value.getFullYear();
  const mesNum = mes.value.getMonth();
  const ultimoDia = new Date(anio, mesNum + 1, 0).getDate();
  const filas: (Celda | null)[][] = [];
  let fila: (Celda | null)[] = [];
  for (let dia = 1; dia <= ultimoDia; dia++) {
    const fecha = new Date(anio, mesNum, dia);
    const dow = fecha.getDay(); // 0 domingo … 6 sábado
    if (dow === 0 || dow === 6) continue;
    if (fila.length === 0 && dow > 1) fila = Array.from({ length: dow - 1 }, () => null);
    const iso = aFechaIso(fecha);
    fila.push({ fecha: iso, dia, estado: porFecha.value.get(iso) });
    if (dow === 5) {
      filas.push(fila);
      fila = [];
    }
  }
  if (fila.length > 0) {
    while (fila.length < 5) fila.push(null);
    filas.push(fila);
  }
  return filas;
});

const resumen = computed(() => {
  const delMes = semanas.value.flat().filter((c): c is Celda => c?.estado !== undefined);
  const contar = (estado: string): number => delMes.filter((c) => c.estado === estado).length;
  return { ausente: contar("ausente"), justificado: contar("justificado"), presente: contar("presente") };
});

const elegida = ref("");
watch(mes, () => (elegida.value = ""));
const detalle = computed(() => {
  const estado = porFecha.value.get(elegida.value);
  return estado ? `${elegida.value}: ${ETIQUETA[estado]}` : "";
});
</script>

<template>
  <div class="asistencia-calendario">
    <div class="asistencia-calendario__barra">
      <button type="button" class="asistencia-calendario__nav" aria-label="Mes anterior" @click="cambiarMes(-1)">
        <ChevronLeft :size="20" aria-hidden="true" />
      </button>
      <h3 class="asistencia-calendario__titulo">{{ titulo }}</h3>
      <button type="button" class="asistencia-calendario__nav" aria-label="Mes siguiente" @click="cambiarMes(1)">
        <ChevronRight :size="20" aria-hidden="true" />
      </button>
    </div>

    <p class="asistencia-calendario__resumen">
      <span>{{ resumen.presente }} presente(s)</span> ·
      <span>{{ resumen.ausente }} ausencia(s)</span> ·
      <span>{{ resumen.justificado }} justificada(s)</span>
    </p>

    <div class="asistencia-calendario__rejilla" role="grid" :aria-label="`Asistencia de ${titulo}`">
      <div v-for="dia in DIAS_SEMANA" :key="dia" class="asistencia-calendario__cabecera" role="columnheader">
        {{ dia }}
      </div>
      <template v-for="(semana, i) in semanas" :key="i">
        <template v-for="(celda, j) in semana" :key="j">
          <div v-if="!celda" class="asistencia-calendario__vacia" />
          <button
            v-else
            type="button"
            class="asistencia-calendario__dia"
            :class="celda.estado ? `asistencia-calendario__dia--${celda.estado}` : ''"
            :aria-label="celda.estado ? `${celda.fecha}: ${ETIQUETA[celda.estado]}` : `${celda.fecha}: sin registro`"
            :disabled="!celda.estado"
            @click="elegida = celda.fecha"
          >
            <span class="asistencia-calendario__numero">{{ celda.dia }}</span>
            <span v-if="celda.estado" class="asistencia-calendario__letra" aria-hidden="true">
              {{ LETRA[celda.estado] }}
            </span>
          </button>
        </template>
      </template>
    </div>

    <p class="asistencia-calendario__leyenda">P presente · A ausente · J justificado</p>
    <p v-if="detalle" class="asistencia-calendario__detalle" aria-live="polite">{{ detalle }}</p>
  </div>
</template>

<style scoped>
.asistencia-calendario__barra {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.asistencia-calendario__titulo {
  margin: 0;
  font-size: var(--texto-base);
  text-transform: capitalize;
}

.asistencia-calendario__nav {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: var(--area-tactil-minima);
  height: var(--area-tactil-minima);
  border: 1px solid var(--color-linea);
  border-radius: var(--radio-md);
  background: var(--color-papel);
  cursor: pointer;
}

.asistencia-calendario__resumen,
.asistencia-calendario__leyenda {
  margin: var(--espacio-xs) 0;
  font-size: var(--texto-sm);
  color: var(--color-tinta-suave);
}

.asistencia-calendario__rejilla {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 4px;
}

.asistencia-calendario__cabecera {
  text-align: center;
  font-size: var(--texto-xs);
  font-weight: 600;
  color: var(--color-tinta-suave);
}

.asistencia-calendario__dia {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  min-height: 3.25rem;
  padding: 0;
  border: 1px solid var(--color-linea);
  border-radius: var(--radio-md);
  background: var(--color-papel);
  font: inherit;
  cursor: pointer;
}

.asistencia-calendario__dia:disabled {
  cursor: default;
  color: var(--color-tinta-suave);
}

.asistencia-calendario__numero {
  font-size: var(--texto-sm);
}

.asistencia-calendario__letra {
  font-size: var(--texto-xs);
  font-weight: 700;
}

.asistencia-calendario__dia--presente {
  background: var(--color-etiqueta-taller-fondo);
  color: var(--color-etiqueta-taller-texto);
}

.asistencia-calendario__dia--ausente {
  background: var(--color-etiqueta-alerta-fondo);
  color: var(--color-etiqueta-alerta-texto);
}

.asistencia-calendario__dia--justificado {
  background: var(--color-etiqueta-aviso-fondo);
  color: var(--color-etiqueta-aviso-texto);
}

.asistencia-calendario__detalle {
  margin: var(--espacio-xs) 0 0;
  font-weight: 600;
}
</style>
