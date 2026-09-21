<script setup lang="ts">
defineProps<{
  items: { valor: string; etiqueta: string }[];
  modelValue: string;
}>();

defineEmits<{ "update:modelValue": [string] }>();
</script>

<template>
  <nav class="bottom-tab-bar" aria-label="Navegación principal">
    <button
      v-for="item in items"
      :key="item.valor"
      type="button"
      class="bottom-tab-bar__item"
      :class="{ 'bottom-tab-bar__item--activo': item.valor === modelValue }"
      :aria-current="item.valor === modelValue ? 'page' : undefined"
      @click="$emit('update:modelValue', item.valor)"
    >
      <slot :name="item.valor" />
      {{ item.etiqueta }}
    </button>
  </nav>
</template>

<style scoped>
.bottom-tab-bar {
  display: flex;
  border-top: 1px solid var(--color-linea);
  padding-bottom: env(safe-area-inset-bottom, 0);
}

.bottom-tab-bar__item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--espacio-2xs);
  min-height: var(--area-tactil-minima);
  padding: var(--espacio-sm) 0;
  background: none;
  border: none;
  font-family: var(--fuente-cuerpo);
  font-size: var(--texto-2xs);
  color: var(--color-tinta-suave);
  cursor: pointer;
}

.bottom-tab-bar__item--activo {
  color: var(--color-accion);
}

.bottom-tab-bar__item:focus-visible {
  outline: 2px solid var(--color-accion);
  outline-offset: -2px;
}
</style>
