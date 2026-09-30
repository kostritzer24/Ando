<script setup lang="ts">
withDefaults(defineProps<{ filas?: number }>(), { filas: 4 });
</script>

<template>
  <!-- Silueta de lo que va a aparecer en vez de un "Cargando…" suelto: la
       página no salta cuando llegan los datos. El texto queda para el
       lector de pantalla. -->
  <div class="cargando-bloque" role="status" aria-live="polite">
    <span class="solo-lector">Cargando…</span>
    <div v-for="n in filas" :key="n" class="cargando-bloque__fila" aria-hidden="true">
      <span class="cargando-bloque__linea cargando-bloque__linea--larga" />
      <span class="cargando-bloque__linea" />
    </div>
  </div>
</template>

<style scoped>
.cargando-bloque {
  background: var(--color-papel);
  border: 1px solid var(--color-linea);
  border-radius: var(--radio-lg);
}

.cargando-bloque__fila {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-sm);
  padding: var(--espacio-lg);
  border-bottom: 1px solid var(--color-linea);
}

.cargando-bloque__fila:last-child {
  border-bottom: none;
}

.cargando-bloque__linea {
  display: block;
  height: 0.75rem;
  width: 35%;
  border-radius: var(--radio-sm);
  background: linear-gradient(90deg, var(--color-hover) 0%, var(--color-linea) 50%, var(--color-hover) 100%);
  background-size: 200% 100%;
  animation: brillo 1.4s ease-in-out infinite;
}

.cargando-bloque__linea--larga {
  width: 60%;
  height: 0.9rem;
}

@keyframes brillo {
  from {
    background-position: 100% 0;
  }
  to {
    background-position: -100% 0;
  }
}
</style>
