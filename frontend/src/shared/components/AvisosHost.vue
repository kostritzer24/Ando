<script setup lang="ts">
import { CircleAlert, CircleCheck, X } from "lucide-vue-next";

import { avisos, cerrarAviso } from "@/shared/composables/useAvisos";
</script>

<template>
  <div class="avisos-host" role="status" aria-live="polite">
    <TransitionGroup name="aviso">
      <div v-for="aviso in avisos" :key="aviso.id" class="avisos-host__aviso" :class="`avisos-host__aviso--${aviso.tipo}`">
        <CircleCheck v-if="aviso.tipo === 'exito'" class="avisos-host__icono" aria-hidden="true" />
        <CircleAlert v-else class="avisos-host__icono" aria-hidden="true" />
        <p class="avisos-host__mensaje">{{ aviso.mensaje }}</p>
        <button type="button" class="avisos-host__cerrar" aria-label="Cerrar aviso" @click="cerrarAviso(aviso.id)">
          <X aria-hidden="true" />
        </button>
      </div>
    </TransitionGroup>
  </div>
</template>

<style scoped>
/* Abajo en el teléfono (donde está el pulgar y no tapa el título),
   abajo a la derecha en escritorio. */
.avisos-host {
  position: fixed;
  z-index: var(--capa-aviso);
  left: var(--espacio-md);
  right: var(--espacio-md);
  bottom: calc(var(--espacio-md) + env(safe-area-inset-bottom, 0px));
  display: flex;
  flex-direction: column;
  gap: var(--espacio-sm);
  pointer-events: none;
}

.avisos-host__aviso {
  pointer-events: auto;
  display: flex;
  align-items: center;
  gap: var(--espacio-sm);
  padding: var(--espacio-xs) var(--espacio-xs) var(--espacio-xs) var(--espacio-md);
  background: var(--color-tinta);
  color: var(--color-papel);
  border-radius: var(--radio-md);
  box-shadow: var(--sombra-flotante);
}

.avisos-host__icono {
  flex: none;
  width: 1.25rem;
  height: 1.25rem;
}

.avisos-host__aviso--exito .avisos-host__icono {
  color: var(--color-exito-sobre-tinta);
}

.avisos-host__aviso--error .avisos-host__icono {
  color: var(--color-peligro-sobre-tinta);
}

.avisos-host__mensaje {
  flex: 1;
  margin: 0;
  font-size: var(--texto-sm);
  font-weight: 500;
}

.avisos-host__cerrar {
  flex: none;
  display: grid;
  place-items: center;
  width: var(--area-tactil-minima);
  height: var(--area-tactil-minima);
  background: none;
  border: none;
  border-radius: var(--radio-sm);
  color: inherit;
  opacity: 0.8;
  cursor: pointer;
}

.avisos-host__cerrar svg {
  width: 1.1rem;
  height: 1.1rem;
}

.avisos-host__cerrar:focus-visible {
  outline-color: var(--color-papel);
}

.aviso-enter-active,
.aviso-leave-active {
  transition:
    opacity var(--transicion),
    transform var(--transicion);
}

.aviso-enter-from,
.aviso-leave-to {
  opacity: 0;
  transform: translateY(8px);
}

@media (min-width: 40rem) {
  .avisos-host {
    left: auto;
    right: var(--espacio-xl);
    bottom: var(--espacio-xl);
    width: 24rem;
  }
}
</style>
