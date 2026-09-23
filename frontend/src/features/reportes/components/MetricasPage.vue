<script setup lang="ts">
import { onMounted, ref } from "vue";

import { ErrorBanner } from "@/shared/components";

import { consultarMetricas } from "../api/reportesApi";
import type { Metricas } from "../api/reportesApi";

const cargando = ref(true);
const error = ref("");
const metricas = ref<Metricas | null>(null);

async function cargar(): Promise<void> {
  cargando.value = true;
  error.value = "";
  try {
    metricas.value = await consultarMetricas();
  } catch {
    error.value = "No se pudieron cargar las métricas. Probá de nuevo.";
  } finally {
    cargando.value = false;
  }
}

onMounted(cargar);
</script>

<template>
  <section class="metricas-page">
    <h1>Métricas del estudio</h1>

    <ErrorBanner v-if="error" :mensaje="error" etiqueta-accion="Reintentar" @accion="cargar" />
    <p v-else-if="cargando">Cargando…</p>

    <template v-else-if="metricas">
      <p class="metricas-page__periodo">
        Semana del {{ new Date(metricas.period_start).toLocaleDateString("es-GT") }} al
        {{ new Date(metricas.period_end).toLocaleDateString("es-GT") }}
      </p>

      <div class="metricas-page__tarjetas">
        <div class="metricas-page__tarjeta">
          <p class="metricas-page__valor">{{ metricas.administrative_processes_percentage }}%</p>
          <p class="metricas-page__etiqueta">Procesos administrativos gestionados por el sistema</p>
        </div>
        <div class="metricas-page__tarjeta">
          <p class="metricas-page__valor">{{ metricas.guardians_portal_usage_percentage }}%</p>
          <p class="metricas-page__etiqueta">Encargados que consultaron el portal esta semana</p>
        </div>
      </div>
    </template>
  </section>
</template>

<style scoped>
.metricas-page h1 {
  font-family: var(--fuente-titulo);
  font-size: var(--texto-md);
  margin: 0 0 var(--espacio-sm);
}

.metricas-page__periodo {
  color: var(--color-tinta-suave);
  margin: 0 0 var(--espacio-xl);
}

.metricas-page__tarjetas {
  display: flex;
  gap: var(--espacio-lg);
  flex-wrap: wrap;
}

.metricas-page__tarjeta {
  flex: 1 1 14rem;
  padding: var(--espacio-lg);
  border-radius: var(--radio-md);
  background: var(--color-fondo);
}

.metricas-page__valor {
  margin: 0;
  font-family: var(--fuente-titulo);
  font-size: var(--texto-xl, 2rem);
  font-weight: 800;
  color: var(--color-accion);
}

.metricas-page__etiqueta {
  margin: var(--espacio-2xs) 0 0;
  color: var(--color-tinta-suave);
}
</style>
