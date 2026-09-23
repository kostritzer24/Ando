<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";

import { usePortalStore } from "@/features/portal/stores/portalStore";
import { EmptyState, ErrorBanner, TagPill } from "@/shared/components";
import type { Attendance } from "@/shared/types/models";

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

const portal = usePortalStore();

const cargando = ref(true);
const error = ref("");
const asistencias = ref<Attendance[]>([]);

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

async function cargar(): Promise<void> {
  if (!portal.estudianteSeleccionadoId) return;
  cargando.value = true;
  error.value = "";
  try {
    asistencias.value = (await attendanceApi.listar()).results;
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
    <h1>Asistencia</h1>

    <ErrorBanner v-if="error" :mensaje="error" etiqueta-accion="Reintentar" @accion="cargar" />
    <p v-else-if="cargando">Cargando…</p>

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
    </template>
  </section>
</template>

<style scoped>
.asistencia-page h1 {
  font-family: var(--fuente-titulo);
  font-size: var(--texto-md);
  margin: 0 0 var(--espacio-lg);
}

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
</style>
