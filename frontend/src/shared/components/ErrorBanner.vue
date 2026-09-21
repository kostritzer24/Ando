<script setup lang="ts">
defineProps<{
  mensaje: string;
  etiquetaAccion?: string;
}>();

defineEmits<{ accion: [] }>();
</script>

<template>
  <div class="error-banner" role="alert">
    <p class="error-banner__mensaje">{{ mensaje }}</p>
    <button v-if="etiquetaAccion" type="button" class="error-banner__accion" @click="$emit('accion')">
      {{ etiquetaAccion }}
    </button>
  </div>
</template>

<style scoped>
/* El error dice qué pasó y qué hacer, sin disculpas (sección 15.2). */
.error-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--espacio-lg);
  background: var(--color-etiqueta-alerta-fondo);
  color: var(--color-etiqueta-alerta-texto);
  border-radius: var(--radio-md);
  padding: var(--espacio-lg);
}

.error-banner__mensaje {
  margin: 0;
  font-size: var(--texto-base);
}

.error-banner__accion {
  background: none;
  border: 1px solid currentColor;
  border-radius: var(--radio-sm);
  color: inherit;
  font-weight: 600;
  font-size: var(--texto-sm);
  padding: 0.35rem 0.7rem;
  white-space: nowrap;
  cursor: pointer;
}

.error-banner__accion:focus-visible {
  outline: 2px solid var(--color-etiqueta-alerta-texto);
  outline-offset: 2px;
}
</style>
