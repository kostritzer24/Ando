<script setup lang="ts">
import { BookOpenText } from "lucide-vue-next";
import { computed, onMounted, ref, watch } from "vue";

import { DIAS, PERIODOS } from "@/features/horarios/api/horariosApi";
import { usePortalStore } from "@/features/portal/stores/portalStore";
import { aFechaIso, fechaLegible } from "@/shared/fechas";
import { AppButton, CargandoBloque, DayTabs, EmptyState, ErrorBanner, PageHeader, TagPill } from "@/shared/components";

import { consultarCalendarioSemanal } from "../api/portalApi";
import type { CalendarioSemanal } from "../api/portalApi";

const portal = usePortalStore();

const cargando = ref(true);
const error = ref("");
const calendario = ref<CalendarioSemanal>({ schedule: [], events: [] });

// Lunes a viernes de la semana real en curso, para el nombre y la fecha
// de cada pestaña, y para saber a qué día del calendario corresponde
// cada evento (los bloques de horario son recurrentes, sin fecha; los
// eventos sí tienen `event_date`).
const hoy = new Date();
const diaSemanaHoy = hoy.getDay(); // 0 domingo … 6 sábado.
const offsetLunes = diaSemanaHoy === 0 ? -6 : 1 - diaSemanaHoy;
const lunes = new Date(hoy);
lunes.setDate(hoy.getDate() + offsetLunes);

// 0 = esta semana, -1 la anterior, 1 la siguiente…
const semanasDeDiferencia = ref(0);

const semana = computed(() =>
  DIAS.map((dia, indice) => {
    const fecha = new Date(lunes);
    fecha.setDate(lunes.getDate() + indice + semanasDeDiferencia.value * 7);
    return {
      valor: dia.valor,
      etiqueta: `${dia.etiqueta.slice(0, 3).toLowerCase()} ${fecha.getDate()}`,
      fechaIso: aFechaIso(fecha),
    };
  }),
);

const rangoDeLaSemana = computed(() => {
  const dias = semana.value;
  return `${fechaLegible(dias[0].fechaIso)} al ${fechaLegible(dias[dias.length - 1].fechaIso)}`;
});

const diaElegido = ref(
  diaSemanaHoy >= 1 && diaSemanaHoy <= 5 ? DIAS[diaSemanaHoy - 1].valor : DIAS[0].valor,
);

interface FilaAgenda {
  hora: string;
  titulo: string;
  detalle: string;
  variante?: "taller" | "aviso";
}

const agendaDelDia = computed<FilaAgenda[]>(() => {
  const fechaIso = semana.value.find((d) => d.valor === diaElegido.value)?.fechaIso;
  const bloques: FilaAgenda[] = calendario.value.schedule
    .filter((b) => b.day_of_week === diaElegido.value)
    .map((b) => ({
      hora: PERIODOS.find((p) => p.numero === b.period_number)?.horario.split("–")[0] ?? "",
      titulo: b.course,
      detalle: b.teacher,
      variante: b.section_type === "taller" ? ("taller" as const) : undefined,
    }));
  const eventos: FilaAgenda[] = calendario.value.events
    .filter((e) => e.event_date === fechaIso)
    .map((e) => ({
      hora: e.start_time.slice(0, 5),
      titulo: e.title,
      detalle: e.type === "institucional" ? "Aviso institucional" : "Asignación docente",
      variante: "aviso" as const,
    }));
  return [...bloques, ...eventos].sort((a, b) => a.hora.localeCompare(b.hora));
});

async function cargar(): Promise<void> {
  if (!portal.estudianteSeleccionadoId) return;
  cargando.value = true;
  error.value = "";
  try {
    calendario.value = await consultarCalendarioSemanal(portal.estudianteSeleccionadoId);
  } catch {
    error.value = "No se pudo cargar el calendario. Inténtalo de nuevo.";
  } finally {
    cargando.value = false;
  }
}

watch(() => portal.estudianteSeleccionadoId, cargar);
onMounted(cargar);
</script>

<template>
  <section class="inicio-page">
    <PageHeader titulo="Calendario de la semana" />

    <RouterLink to="/portal/convivencia" class="inicio-page__convivencia">
      <BookOpenText aria-hidden="true" />
      <span>
        <strong>Código de convivencia 2026</strong>
        <small>Conoce las normas del centro y qué pasa cuando no se cumplen.</small>
      </span>
    </RouterLink>

    <ErrorBanner v-if="error" :mensaje="error" etiqueta-accion="Reintentar" @accion="cargar" />
    <CargandoBloque v-else-if="cargando" />

    <template v-else>
      <div class="inicio-page__semana">
        <AppButton variante="discreto" compacto @click="semanasDeDiferencia--">‹ Anterior</AppButton>
        <button
          type="button"
          class="inicio-page__rango"
          :disabled="semanasDeDiferencia === 0"
          @click="semanasDeDiferencia = 0"
        >
          {{ semanasDeDiferencia === 0 ? "Esta semana" : "Volver a esta semana" }}
          <small>{{ rangoDeLaSemana }}</small>
        </button>
        <AppButton variante="discreto" compacto @click="semanasDeDiferencia++">Siguiente ›</AppButton>
      </div>
      <DayTabs :dias="semana" v-model="diaElegido" />

      <EmptyState
        v-if="agendaDelDia.length === 0"
        titulo="Sin clases ni avisos"
        descripcion="No hay nada agendado para este día."
      />
      <ul v-else class="inicio-page__agenda">
        <li v-for="(fila, indice) in agendaDelDia" :key="indice" class="inicio-page__fila">
          <span class="inicio-page__hora">{{ fila.hora }}</span>
          <div class="inicio-page__info">
            <p class="inicio-page__titulo">{{ fila.titulo }}</p>
            <p class="inicio-page__detalle">{{ fila.detalle }}</p>
          </div>
          <TagPill v-if="fila.variante" :variante="fila.variante">
            {{ fila.variante === "taller" ? "Taller" : "Aviso" }}
          </TagPill>
        </li>
      </ul>
    </template>
  </section>
</template>

<style scoped>
.inicio-page__semana {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--espacio-sm);
  margin-bottom: var(--espacio-md);
}

.inicio-page__rango {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: none;
  border: none;
  color: var(--color-tinta);
  font-size: var(--texto-sm);
  font-weight: 600;
  cursor: pointer;
}

.inicio-page__rango:disabled {
  cursor: default;
}

.inicio-page__rango small {
  color: var(--color-tinta-suave);
  font-weight: 400;
}

.inicio-page__convivencia {
  display: flex;
  align-items: center;
  gap: var(--espacio-md);
  margin-bottom: var(--espacio-lg);
  padding: var(--espacio-md);
  border: 1px solid var(--color-linea);
  border-radius: var(--radio-md);
  color: var(--color-tinta);
  text-decoration: none;
}

.inicio-page__convivencia svg {
  flex: none;
  width: 1.5rem;
  height: 1.5rem;
}

.inicio-page__convivencia small {
  display: block;
  margin-top: var(--espacio-2xs);
  font-size: var(--texto-sm);
  color: var(--color-tinta-suave);
}

.inicio-page__agenda {
  list-style: none;
  margin: var(--espacio-lg) 0 0;
  padding: 0;
}

.inicio-page__fila {
  display: grid;
  grid-template-columns: 3.4rem 1fr auto;
  align-items: baseline;
  gap: var(--espacio-md);
  padding: var(--espacio-sm) 0;
  border-bottom: 1px solid var(--color-linea);
}

.inicio-page__hora {
  font-variant-numeric: tabular-nums;
  font-size: var(--texto-sm);
  color: var(--color-tinta-suave);
}

.inicio-page__titulo {
  margin: 0;
  font-weight: 600;
}

.inicio-page__detalle {
  margin: 0.1rem 0 0;
  font-size: var(--texto-sm);
  color: var(--color-tinta-suave);
}
</style>
