<script setup lang="ts">
import { useId } from "vue";

defineProps<{ titulo?: string; descripcion?: string }>();
const idTitulo = useId();
</script>

<template>
  <!-- Un bloque de trabajo dentro de una pantalla (un formulario, un paso,
       una lista con título). Una sola forma para todos: fondo blanco, línea
       fina, sin sombra (sección 15.4). -->
  <section class="app-panel" :aria-labelledby="titulo ? idTitulo : undefined">
    <header v-if="titulo || $slots.acciones" class="app-panel__cabecera">
      <div>
        <h2 v-if="titulo" :id="idTitulo" class="app-panel__titulo">{{ titulo }}</h2>
        <p v-if="descripcion" class="app-panel__descripcion">{{ descripcion }}</p>
      </div>
      <div v-if="$slots.acciones" class="app-panel__acciones"><slot name="acciones" /></div>
    </header>
    <slot />
  </section>
</template>

<style scoped>
.app-panel {
  min-width: 0;
  padding: var(--espacio-lg);
  background: var(--color-papel);
  border: 1px solid var(--color-linea);
  border-radius: var(--radio-lg);
}

.app-panel__cabecera {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--espacio-md);
  margin-bottom: var(--espacio-lg);
}

.app-panel__titulo {
  font-size: var(--texto-md);
}

.app-panel__descripcion {
  margin: var(--espacio-2xs) 0 0;
  font-size: var(--texto-sm);
  color: var(--color-tinta-suave);
}

.app-panel__acciones {
  flex: none;
}

@media (min-width: 40rem) {
  .app-panel {
    padding: var(--espacio-xl) var(--espacio-2xl);
  }
}
</style>
