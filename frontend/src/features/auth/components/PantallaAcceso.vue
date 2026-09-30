<script setup lang="ts">
defineProps<{ titulo: string; subtitulo: string }>();
</script>

<template>
  <!-- Mobile-first: en el teléfono la pantalla entera es blanca y el
       formulario empieza arriba (el teclado no tapa nada); desde 40rem es
       un panel centrado sobre el fondo gris. Es la única pantalla donde
       aparece el logo completo — el "elemento memorable" de la sección
       15.4 —, así que todo lo demás se queda callado. -->
  <main class="pantalla-acceso">
    <div class="pantalla-acceso__panel">
      <img
        class="pantalla-acceso__logo"
        src="/logo-completo.png"
        alt="El Patojismo — Sueños e ideas en acción"
        width="480"
        height="457"
      />
      <h1 class="pantalla-acceso__titulo">{{ titulo }}</h1>
      <p class="pantalla-acceso__subtitulo">{{ subtitulo }}</p>
      <slot />
    </div>
    <p class="pantalla-acceso__pie">Centro Socioeducativo Lic. Magno Rudy Romero Arévalo</p>
  </main>
</template>

<style scoped>
.pantalla-acceso {
  min-height: 100vh;
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  align-items: center;
  background: var(--color-papel);
  padding: var(--espacio-3xl) var(--espacio-lg) var(--espacio-xl);
}

.pantalla-acceso__panel {
  width: 100%;
  max-width: 24rem;
  display: flex;
  flex-direction: column;
  gap: var(--espacio-lg);
}

.pantalla-acceso__logo {
  width: 8.5rem;
  height: auto;
  margin: 0 auto var(--espacio-lg);
}

.pantalla-acceso__titulo {
  font-size: var(--texto-titulo);
}

.pantalla-acceso__subtitulo {
  margin: calc(-1 * var(--espacio-sm)) 0 var(--espacio-sm);
  color: var(--color-tinta-suave);
}

.pantalla-acceso__pie {
  margin: auto 0 0;
  padding-top: var(--espacio-3xl);
  font-size: var(--texto-xs);
  color: var(--color-tinta-suave);
  text-align: center;
}

@media (min-width: 40rem) {
  .pantalla-acceso {
    justify-content: center;
    background: var(--color-fondo);
    padding-top: var(--espacio-4xl);
  }

  .pantalla-acceso__panel {
    max-width: 26rem;
    padding: var(--espacio-3xl);
    background: var(--color-papel);
    border: 1px solid var(--color-linea);
    border-radius: var(--radio-lg);
  }

  .pantalla-acceso__pie {
    margin-top: 0;
  }
}
</style>
