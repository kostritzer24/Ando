<script setup lang="ts">
import { CircleAlert } from "lucide-vue-next";

defineProps<{
  mensaje: string;
  etiquetaAccion?: string;
}>();

defineEmits<{ accion: [] }>();
</script>

<template>
  <div class="error-banner" role="alert">
    <CircleAlert class="error-banner__icono" aria-hidden="true" />
    <p class="error-banner__mensaje">{{ mensaje }}</p>
    <button v-if="etiquetaAccion" type="button" class="error-banner__accion" @click="$emit('accion')">
      {{ etiquetaAccion }}
    </button>
  </div>
</template>

<style scoped>
/* El error dice qué pasó y qué hacer, sin disculpas (sección 15.2).
   En el teléfono la acción baja debajo del mensaje. */
.error-banner {
  display: grid;
  grid-template-columns: auto 1fr;
  align-items: start;
  gap: var(--espacio-sm) var(--espacio-md);
  background: var(--color-etiqueta-alerta-fondo);
  color: var(--color-etiqueta-alerta-texto);
  border-left: 4px solid var(--color-peligro);
  border-radius: var(--radio-md);
  padding: var(--espacio-md) var(--espacio-lg);
  margin-bottom: var(--espacio-lg);
}

.error-banner__icono {
  width: 1.25rem;
  height: 1.25rem;
  margin-top: 0.1rem;
}

.error-banner__mensaje {
  margin: 0;
  font-size: var(--texto-sm);
  font-weight: 500;
}

.error-banner__accion {
  grid-column: 2;
  justify-self: start;
  min-height: 2.5rem;
  background: var(--color-papel);
  border: 1px solid currentColor;
  border-radius: var(--radio-sm);
  color: inherit;
  font-weight: 600;
  font-size: var(--texto-sm);
  padding: 0 var(--espacio-md);
  white-space: nowrap;
  cursor: pointer;
}

.error-banner__accion:focus-visible {
  outline: 2px solid var(--color-etiqueta-alerta-texto);
  outline-offset: 2px;
}

@media (min-width: 40rem) {
  .error-banner {
    grid-template-columns: auto 1fr auto;
    align-items: center;
  }

  .error-banner__icono {
    margin-top: 0;
  }

  .error-banner__accion {
    grid-column: 3;
  }
}
</style>
