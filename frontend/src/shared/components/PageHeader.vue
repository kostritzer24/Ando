<script setup lang="ts">
import { ChevronLeft } from "lucide-vue-next";

defineProps<{
  titulo: string;
  descripcion?: string;
  /** Ruta de la pantalla anterior cuando esta es un detalle (expediente,
   * unidades de un ciclo) — en el teléfono no hay otra forma visible de
   * volver sin abrir el menú. */
  volverA?: string;
  etiquetaVolver?: string;
}>();
</script>

<template>
  <header class="page-header">
    <RouterLink v-if="volverA" :to="volverA" class="page-header__volver">
      <ChevronLeft aria-hidden="true" />
      {{ etiquetaVolver ?? "Volver" }}
    </RouterLink>
    <div class="page-header__fila">
      <div class="page-header__textos">
        <h1 class="page-header__titulo">{{ titulo }}</h1>
        <p v-if="descripcion" class="page-header__descripcion">{{ descripcion }}</p>
        <slot name="detalle" />
      </div>
      <div v-if="$slots.acciones" class="page-header__acciones">
        <slot name="acciones" />
      </div>
    </div>
  </header>
</template>

<style scoped>
/* Una sola forma de encabezar una pantalla en todo el sistema: título,
   una línea opcional de contexto y la acción principal. En el teléfono la
   acción baja debajo del título y ocupa el ancho; desde 40rem se alinea a
   la derecha. */
.page-header {
  margin-bottom: var(--espacio-2xl);
}

.page-header__volver {
  display: inline-flex;
  align-items: center;
  gap: var(--espacio-2xs);
  min-height: var(--area-tactil-minima);
  margin: calc(-1 * var(--espacio-sm)) 0 var(--espacio-2xs) calc(-1 * var(--espacio-xs));
  font-size: var(--texto-sm);
  font-weight: 600;
  color: var(--color-accion);
  text-decoration: none;
}

.page-header__volver:hover {
  text-decoration: underline;
}

.page-header__volver svg {
  width: 1.1rem;
  height: 1.1rem;
}

.page-header__fila {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-lg);
}

.page-header__textos {
  min-width: 0;
}

.page-header__descripcion {
  margin: var(--espacio-xs) 0 0;
  color: var(--color-tinta-suave);
  max-width: 60ch;
}

.page-header__acciones {
  display: flex;
  flex-wrap: wrap;
  gap: var(--espacio-sm);
}

.page-header__acciones > :deep(*) {
  flex: 1 1 auto;
}

@media (min-width: 40rem) {
  .page-header__fila {
    flex-direction: row;
    align-items: flex-end;
    justify-content: space-between;
  }

  .page-header__acciones {
    flex: none;
  }

  .page-header__acciones > :deep(*) {
    flex: none;
  }
}
</style>
