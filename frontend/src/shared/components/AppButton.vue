<script setup lang="ts">
withDefaults(
  defineProps<{
    /** `peligro` es solo para la acción que confirma algo destructivo;
     * `discreto` es la acción de fila (texto con color, sin borde). */
    variante?: "primario" | "secundario" | "peligro" | "discreto";
    tipo?: "button" | "submit";
    deshabilitado?: boolean;
    /** Ocupa todo el ancho disponible — el botón principal de un
     * formulario en el teléfono. */
    bloque?: boolean;
    compacto?: boolean;
  }>(),
  {
    variante: "primario",
    tipo: "button",
    deshabilitado: false,
    bloque: false,
    compacto: false,
  },
);

defineEmits<{ click: [MouseEvent] }>();
</script>

<template>
  <button
    :type="tipo"
    class="app-button"
    :class="[
      `app-button--${variante}`,
      { 'app-button--bloque': bloque, 'app-button--compacto': compacto },
    ]"
    :disabled="deshabilitado"
    @click="$emit('click', $event)"
  >
    <slot />
  </button>
</template>

<style scoped>
.app-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--espacio-sm);
  min-height: var(--area-tactil-minima);
  padding: 0 var(--espacio-lg);
  border-radius: var(--radio-md);
  border: 1px solid transparent;
  font-family: var(--fuente-cuerpo);
  font-size: var(--texto-base);
  font-weight: 600;
  line-height: 1.2;
  text-align: center;
  cursor: pointer;
  transition:
    background-color var(--transicion),
    border-color var(--transicion),
    color var(--transicion);
}

.app-button :deep(svg) {
  flex: none;
  width: 1.15em;
  height: 1.15em;
}

.app-button:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.app-button:focus-visible {
  outline: 2px solid var(--color-accion);
  outline-offset: 2px;
}

.app-button--bloque {
  display: flex;
  width: 100%;
}

.app-button--compacto {
  font-size: var(--texto-sm);
  padding: 0 var(--espacio-md);
}

.app-button--primario {
  background: var(--color-accion);
  color: var(--color-papel);
}

.app-button--primario:hover:not(:disabled) {
  background: var(--color-accion-hover);
}

.app-button--secundario {
  background: var(--color-papel);
  color: var(--color-accion);
  border-color: var(--color-linea-fuerte);
}

.app-button--secundario:hover:not(:disabled) {
  background: var(--color-accion-suave);
  border-color: var(--color-accion);
}

.app-button--peligro {
  background: var(--color-peligro);
  color: var(--color-papel);
}

.app-button--peligro:hover:not(:disabled) {
  background: var(--color-peligro-hover);
}

.app-button--peligro:focus-visible {
  outline-color: var(--color-peligro);
}

.app-button--discreto {
  background: none;
  color: var(--color-accion);
  padding: 0 var(--espacio-sm);
}

.app-button--discreto:hover:not(:disabled) {
  background: var(--color-accion-suave);
}
</style>
