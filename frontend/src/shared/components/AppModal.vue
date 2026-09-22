<script setup lang="ts">
defineProps<{ titulo: string }>();
const emit = defineEmits<{ cerrar: [] }>();

function alHacerClicEnFondo(evento: MouseEvent): void {
  if (evento.target === evento.currentTarget) {
    emit("cerrar");
  }
}
</script>

<template>
  <div class="app-modal__fondo" @click="alHacerClicEnFondo" @keydown.esc="emit('cerrar')">
    <div class="app-modal" role="dialog" :aria-label="titulo">
      <header class="app-modal__cabecera">
        <h2 class="app-modal__titulo">{{ titulo }}</h2>
        <button type="button" class="app-modal__cerrar" aria-label="Cerrar" @click="emit('cerrar')">
          ✕
        </button>
      </header>
      <div class="app-modal__cuerpo">
        <slot />
      </div>
    </div>
  </div>
</template>

<style scoped>
.app-modal__fondo {
  position: fixed;
  inset: 0;
  background: rgb(20 24 28 / 45%);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 3rem 1rem;
  z-index: 100;
  overflow-y: auto;
}

.app-modal {
  background: var(--color-papel);
  border-radius: var(--radio-lg);
  width: 100%;
  max-width: 30rem;
}

.app-modal__cabecera {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--espacio-lg) var(--espacio-xl);
  border-bottom: 1px solid var(--color-linea);
}

.app-modal__titulo {
  font-family: var(--fuente-titulo);
  font-size: var(--texto-md);
  font-weight: 700;
  margin: 0;
}

.app-modal__cerrar {
  min-width: var(--area-tactil-minima);
  min-height: var(--area-tactil-minima);
  background: none;
  border: none;
  font-size: var(--texto-md);
  color: var(--color-tinta-suave);
  cursor: pointer;
}

.app-modal__cerrar:focus-visible {
  outline: 2px solid var(--color-accion);
}

.app-modal__cuerpo {
  padding: var(--espacio-xl);
  display: flex;
  flex-direction: column;
  gap: var(--espacio-lg);
}
</style>
