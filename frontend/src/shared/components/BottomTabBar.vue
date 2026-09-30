<script setup lang="ts">
import type { Component } from "vue";

defineProps<{
  items: { valor: string; etiqueta: string; icono?: Component }[];
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
      <component :is="item.icono" v-if="item.icono" class="bottom-tab-bar__icono" aria-hidden="true" />
      <slot :name="item.valor" />
      {{ item.etiqueta }}
    </button>
  </nav>
</template>

<style scoped>
/* Fija abajo: en el teléfono es la navegación principal, tiene que estar
   al alcance del pulgar aunque la pantalla sea larga. */
.bottom-tab-bar {
  position: sticky;
  bottom: 0;
  z-index: var(--capa-barra);
  display: flex;
  background: var(--color-papel);
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
  font-size: var(--texto-xs);
  font-weight: 500;
  color: var(--color-tinta-suave);
  cursor: pointer;
}

.bottom-tab-bar__icono {
  width: 1.35rem;
  height: 1.35rem;
}

.bottom-tab-bar__item--activo {
  color: var(--color-accion);
  font-weight: 700;
}

.bottom-tab-bar__item:focus-visible {
  outline: 2px solid var(--color-accion);
  outline-offset: -2px;
}
</style>
