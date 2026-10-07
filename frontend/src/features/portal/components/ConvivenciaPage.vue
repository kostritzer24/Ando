<script setup lang="ts">
import { manualConvivencia as manual } from "../data/manualConvivencia";

// El manual marca el tipo de falta al inicio del párrafo ("Faltas Leves: …"):
// se resalta para que la familia lo encuentre al leer rápido.
function partirEtiqueta(parrafo: string): { etiqueta: string; resto: string } {
  const coincidencia = /^(Faltas [^:]+:)(.*)$/.exec(parrafo);
  return coincidencia
    ? { etiqueta: coincidencia[1], resto: coincidencia[2] }
    : { etiqueta: "", resto: parrafo };
}
</script>

<template>
  <section class="convivencia-page">
    <header class="convivencia-page__encabezado">
      <h1>{{ manual.titulo }}</h1>
      <p class="convivencia-page__institucion">{{ manual.institucion }}</p>
    </header>

    <h2>Introducción</h2>
    <p v-for="parrafo in manual.introduccion" :key="parrafo">{{ parrafo }}</p>

    <h2>Principios fundamentales</h2>
    <ul class="convivencia-page__principios">
      <li v-for="principio in manual.principios" :key="principio.titulo">
        <strong>{{ principio.titulo }}:</strong> {{ principio.texto }}
      </li>
    </ul>

    <details v-for="(capitulo, indice) in manual.capitulos" :key="capitulo.titulo" class="convivencia-page__capitulo" :open="indice === 0">
      <summary>{{ capitulo.titulo }}</summary>
      <article v-for="articulo in capitulo.articulos" :key="articulo.numero" class="convivencia-page__articulo">
        <h3>{{ articulo.numero }}. {{ articulo.titulo }}</h3>
        <p v-for="parrafo in articulo.parrafos" :key="parrafo">
          <strong>{{ partirEtiqueta(parrafo).etiqueta }}</strong>{{ partirEtiqueta(parrafo).resto }}
        </p>
        <ul v-if="articulo.items.length > 0">
          <li v-for="item in articulo.items" :key="item">{{ item }}</li>
        </ul>
      </article>
    </details>

    <footer class="convivencia-page__cierre">
      <p v-for="parrafo in manual.cierre" :key="parrafo">{{ parrafo }}</p>
    </footer>
  </section>
</template>

<style scoped>
.convivencia-page h1 {
  font-family: var(--fuente-titulo);
  font-size: var(--texto-lg);
  margin: 0;
}

.convivencia-page h2 {
  font-family: var(--fuente-titulo);
  font-size: var(--texto-base);
  margin: var(--espacio-xl) 0 var(--espacio-sm);
}

.convivencia-page p {
  margin: 0 0 var(--espacio-sm);
  line-height: 1.5;
}

.convivencia-page__institucion {
  margin-top: var(--espacio-2xs);
  color: var(--color-tinta-suave);
}

.convivencia-page__principios {
  margin: 0;
  padding-left: var(--espacio-lg);
  line-height: 1.5;
}

.convivencia-page__capitulo {
  margin-top: var(--espacio-lg);
  border-top: 1px solid var(--color-linea);
}

.convivencia-page__capitulo summary {
  padding: var(--espacio-md) 0;
  min-height: var(--area-tactil-minima);
  font-weight: 700;
  cursor: pointer;
}

.convivencia-page__articulo {
  padding-bottom: var(--espacio-md);
}

.convivencia-page__articulo h3 {
  font-size: var(--texto-base);
  margin: var(--espacio-md) 0 var(--espacio-xs);
}

.convivencia-page__articulo ul {
  margin: 0 0 var(--espacio-sm);
  padding-left: var(--espacio-lg);
  line-height: 1.5;
}

.convivencia-page__cierre {
  margin-top: var(--espacio-xl);
  padding-top: var(--espacio-md);
  border-top: 1px solid var(--color-linea);
  color: var(--color-tinta-suave);
  font-size: var(--texto-sm);
}
</style>
