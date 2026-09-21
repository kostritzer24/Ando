<script setup lang="ts">
withDefaults(defineProps<{ sinLinea?: boolean }>(), { sinLinea: false });
</script>

<template>
  <div class="list-row" :class="{ 'list-row--sin-linea': sinLinea }">
    <span v-if="$slots.tiempo" class="list-row__tiempo">
      <slot name="tiempo" />
    </span>
    <div class="list-row__contenido">
      <slot />
    </div>
    <span v-if="$slots.final" class="list-row__final">
      <slot name="final" />
    </span>
  </div>
</template>

<style scoped>
/* Fila con línea inferior, nunca una tarjeta con sombra — sección 15.4
   del prompt maestro: "sin tarjetas idénticas con la misma sombra". */
.list-row {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: baseline;
  gap: var(--espacio-xl);
  padding: var(--espacio-md) 0;
  border-bottom: 1px solid var(--color-linea);
  min-height: var(--area-tactil-minima);
}

.list-row--sin-linea {
  border-bottom: none;
}

.list-row__tiempo {
  font-variant-numeric: tabular-nums;
  font-size: var(--texto-sm);
  color: var(--color-tinta-suave);
}

.list-row__contenido {
  min-width: 0;
}

.list-row__final {
  align-self: center;
}
</style>
