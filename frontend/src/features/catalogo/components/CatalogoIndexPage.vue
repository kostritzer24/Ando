<script setup lang="ts">
import { PageHeader } from "@/shared/components";
const catalogos = [
  { a: "/administrativo/catalogo/ciclos", etiqueta: "Ciclos escolares y unidades" },
  { a: "/administrativo/catalogo/secciones", etiqueta: "Secciones" },
  { a: "/administrativo/catalogo/cursos", etiqueta: "Cursos" },
  { a: "/administrativo/catalogo/tipos-actividad", etiqueta: "Tipos de actividad evaluativa" },
  { a: "/administrativo/catalogo/tipos-justificacion", etiqueta: "Tipos de justificación" },
  { a: "/administrativo/catalogo/tipos-documento", etiqueta: "Tipos de documento" },
  { a: "/administrativo/catalogo/becas", etiqueta: "Becas" },
  { a: "/administrativo/catalogo/articulos-convivencia", etiqueta: "Artículos del código de convivencia" },
];
</script>

<template>
  <section class="catalogo-index">
    <PageHeader titulo="Datos maestros" />
    <nav class="catalogo-index__lista">
      <RouterLink v-for="item in catalogos" :key="item.a" :to="item.a" class="catalogo-index__enlace">
        {{ item.etiqueta }}
      </RouterLink>
    </nav>
  </section>
</template>

<style scoped>

.catalogo-index__lista {
  display: flex;
  flex-direction: column;
}

.catalogo-index__enlace {
  min-height: var(--area-tactil-minima);
  display: flex;
  align-items: center;
  padding: 0 var(--espacio-md);
  border-bottom: 1px solid var(--color-linea);
  color: var(--color-tinta);
  text-decoration: none;
  font-size: var(--texto-base);
}

.catalogo-index__enlace:hover {
  color: var(--color-accion);
}
</style>
