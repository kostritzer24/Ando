<script setup lang="ts">
defineProps<{
  nombreEstudiante: string;
  nombreSeccion: string;
}>();

defineEmits<{ "cambiar-estudiante": [] }>();
</script>

<template>
  <header class="top-app-bar">
    <div class="top-app-bar__marca">
      <slot name="marca" />
      <span>El Patojismo</span>
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
  padding: 0 var(--espacio-xl) var(--espacio-lg);
  border-bottom: 1px solid var(--color-linea);
}

.top-app-bar__marca {
  display: flex;
  align-items: center;
  gap: var(--espacio-sm);
  margin-bottom: var(--espacio-lg);
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
