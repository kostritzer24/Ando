<script setup lang="ts">
defineProps<{
  titulo: string;
  descripcion: string;
  etiquetaAccion?: string;
}>();

defineEmits<{ accion: [] }>();
</script>

<template>
  <div class="empty-state">
    <p class="empty-state__titulo">{{ titulo }}</p>
    <p class="empty-state__descripcion">{{ descripcion }}</p>
    <button v-if="etiquetaAccion" type="button" class="empty-state__accion" @click="$emit('accion')">
      {{ etiquetaAccion }}
    </button>
  </div>
</template>

<style scoped>
/* La pantalla vacía invita a la acción siguiente (sección 15.2). */
.empty-state {
  text-align: center;
  padding: 2rem 1rem;
}

.empty-state__titulo {
  font-family: var(--fuente-titulo);
  font-weight: 700;
  font-size: var(--texto-md);
  margin: 0 0 var(--espacio-xs);
}

.empty-state__descripcion {
  color: var(--color-tinta-suave);
  font-size: var(--texto-base);
  margin: 0 0 var(--espacio-lg);
}

.empty-state__accion {
  min-height: var(--area-tactil-minima);
  padding: 0 1rem;
  border-radius: var(--radio-md);
  background: var(--color-accion);
  color: var(--color-papel);
  border: none;
  font-weight: 600;
  cursor: pointer;
}

.empty-state__accion:focus-visible {
  outline: 2px solid var(--color-accion);
  outline-offset: 2px;
}
</style>
