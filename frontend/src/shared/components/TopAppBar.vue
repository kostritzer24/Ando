<script setup lang="ts">
defineProps<{
  nombreEstudiante: string;
  nombreSeccion: string;
}>();

defineEmits<{ "cambiar-estudiante": [] }>();
</script>

<template>
  <header class="top-app-bar">
    <div class="top-app-bar__fila-marca">
      <div class="top-app-bar__marca">
        <slot name="marca" />
        <span>El Patojismo</span>
      </div>
      <slot name="acciones" />
    </div>
    <div class="top-app-bar__estudiante">
      <div class="top-app-bar__nombre">
        <p class="top-app-bar__nombre-texto">{{ nombreEstudiante }}</p>
        <p class="top-app-bar__seccion">{{ nombreSeccion }}</p>
      </div>
      <button type="button" class="top-app-bar__cambiar" @click="$emit('cambiar-estudiante')">
        Cambiar estudiante
      </button>
    </div>
  </header>
</template>

<style scoped>
.top-app-bar {
  padding: var(--espacio-xs) var(--espacio-lg) var(--espacio-md);
  padding-top: calc(var(--espacio-xs) + env(safe-area-inset-top, 0px));
  background: var(--color-papel);
  border-bottom: 1px solid var(--color-linea);
}

.top-app-bar__fila-marca {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--espacio-md);
  min-height: var(--area-tactil-minima);
  margin-bottom: var(--espacio-sm);
}

.top-app-bar__marca {
  display: flex;
  align-items: center;
  gap: var(--espacio-sm);
  font-family: var(--fuente-titulo);
  font-weight: 700;
  font-size: var(--texto-base);
}

.top-app-bar__estudiante {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--espacio-lg);
}

.top-app-bar__nombre {
  min-width: 0;
}

.top-app-bar__nombre-texto {
  margin: 0;
  font-weight: 600;
  font-size: var(--texto-base);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.top-app-bar__seccion {
  margin: 0.1rem 0 0;
  font-size: var(--texto-sm);
  color: var(--color-tinta-suave);
}

.top-app-bar__cambiar {
  flex: none;
  min-height: var(--area-tactil-minima);
  font-family: var(--fuente-cuerpo);
  font-size: var(--texto-sm);
  font-weight: 600;
  color: var(--color-accion);
  background: none;
  border: 1px solid var(--color-linea);
  border-radius: var(--radio-sm);
  padding: 0 0.7rem;
  cursor: pointer;
}

.top-app-bar__cambiar:focus-visible {
  outline: 2px solid var(--color-accion);
  outline-offset: 2px;
}
</style>
