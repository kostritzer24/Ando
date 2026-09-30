<script setup lang="ts">
withDefaults(
  defineProps<{
    variante?: "taller" | "aviso" | "hoy" | "alerta" | "neutro";
  }>(),
  { variante: "hoy" },
);
</script>

<template>
  <span class="tag-pill" :class="`tag-pill--${variante}`">
    <slot />
  </span>
</template>

<style scoped>
.tag-pill {
  display: inline-block;
  font-family: var(--fuente-cuerpo);
  font-size: var(--texto-xs);
  font-weight: 600;
  padding: 0.2rem 0.55rem;
  border-radius: var(--radio-sm);
  white-space: nowrap;
}

.tag-pill--taller {
  background: var(--color-etiqueta-taller-fondo);
  color: var(--color-etiqueta-taller-texto);
}

.tag-pill--aviso {
  background: var(--color-etiqueta-aviso-fondo);
  color: var(--color-etiqueta-aviso-texto);
}

.tag-pill--hoy {
  background: var(--color-etiqueta-hoy-fondo);
  color: var(--color-etiqueta-hoy-texto);
}

.tag-pill--neutro {
  background: var(--color-hover);
  color: var(--color-tinta-suave);
}

.tag-pill--alerta {
  background: var(--color-etiqueta-alerta-fondo);
  color: var(--color-etiqueta-alerta-texto);
}
</style>
