<script setup lang="ts">
withDefaults(
  defineProps<{
    variante?: "primario" | "secundario";
    tipo?: "button" | "submit";
    deshabilitado?: boolean;
  }>(),
  {
    variante: "primario",
    tipo: "button",
    deshabilitado: false,
  },
);

defineEmits<{ click: [MouseEvent] }>();
</script>

<template>
  <button
    :type="tipo"
    class="app-button"
    :class="`app-button--${variante}`"
    :disabled="deshabilitado"
    @click="$emit('click', $event)"
  >
    <slot />
  </button>
</template>

<style scoped>
.app-button {
  min-height: var(--area-tactil-minima);
  padding: 0 1rem;
  border-radius: var(--radio-md);
  font-family: var(--fuente-cuerpo);
  font-size: var(--texto-base);
  font-weight: 600;
  cursor: pointer;
}

.app-button:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.app-button:focus-visible {
  outline: 2px solid var(--color-accion);
  outline-offset: 2px;
}

.app-button--primario {
  background: var(--color-accion);
  color: var(--color-papel);
  border: 1px solid var(--color-accion);
}

.app-button--secundario {
  background: var(--color-papel);
  color: var(--color-accion);
  border: 1px solid var(--color-linea);
}
</style>
