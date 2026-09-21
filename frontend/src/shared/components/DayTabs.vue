<script setup lang="ts">
defineProps<{
  dias: { valor: string; etiqueta: string }[];
  modelValue: string;
}>();

defineEmits<{ "update:modelValue": [string] }>();
</script>

<template>
  <nav class="day-tabs" aria-label="Selector de día">
    <button
      v-for="dia in dias"
      :key="dia.valor"
      type="button"
      class="day-tabs__boton"
      :class="{ 'day-tabs__boton--activo': dia.valor === modelValue }"
      :aria-current="dia.valor === modelValue ? 'true' : undefined"
      @click="$emit('update:modelValue', dia.valor)"
    >
      {{ dia.etiqueta }}
    </button>
  </nav>
</template>

<style scoped>
.day-tabs {
  display: flex;
  gap: var(--espacio-xl);
  overflow-x: auto;
  border-bottom: 1px solid var(--color-linea);
}

.day-tabs__boton {
  flex: none;
  min-height: var(--area-tactil-minima);
  background: none;
  border: none;
  border-bottom: 3px solid transparent;
  font-family: var(--fuente-cuerpo);
  font-size: var(--texto-sm);
  color: var(--color-tinta-suave);
  cursor: pointer;
}

.day-tabs__boton--activo {
  color: var(--color-tinta);
  font-weight: 700;
  border-color: var(--color-accion);
}

.day-tabs__boton:focus-visible {
  outline: 2px solid var(--color-accion);
  outline-offset: -2px;
}
</style>
