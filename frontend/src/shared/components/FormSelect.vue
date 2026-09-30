<script setup lang="ts">
withDefaults(
  defineProps<{
    id: string;
    etiqueta: string;
    modelValue: string;
    opciones: { valor: string; etiqueta: string }[];
    placeholder?: string;
    mensajeError?: string;
  }>(),
  { placeholder: "Elegí una opción" },
);

defineEmits<{ "update:modelValue": [string] }>();
</script>

<template>
  <div class="form-select">
    <label :for="id" class="form-select__etiqueta">{{ etiqueta }}</label>
    <select
      :id="id"
      class="form-select__input"
      :value="modelValue"
      :aria-invalid="Boolean(mensajeError)"
      @change="$emit('update:modelValue', ($event.target as HTMLSelectElement).value)"
    >
      <option value="" disabled>{{ placeholder }}</option>
      <option v-for="opcion in opciones" :key="opcion.valor" :value="opcion.valor">
        {{ opcion.etiqueta }}
      </option>
    </select>
    <p v-if="mensajeError" class="form-select__error" role="alert">{{ mensajeError }}</p>
  </div>
</template>

<style scoped>
.form-select {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-xs);
}

.form-select__etiqueta {
  font-family: var(--fuente-cuerpo);
  font-weight: 600;
  font-size: var(--texto-sm);
}

.form-select__input {
  width: 100%;
  min-height: var(--area-tactil-minima);
  padding: 0 0.75rem;
  border: 1px solid var(--color-borde-campo);
  border-radius: var(--radio-md);
  font-family: var(--fuente-cuerpo);
  font-size: var(--texto-base);
  background: var(--color-papel);
  color: var(--color-tinta);
}

.form-select__input:focus-visible {
  outline: 2px solid var(--color-accion);
  outline-offset: 1px;
  border-color: var(--color-accion);
}

.form-select__input[aria-invalid="true"] {
  border-color: var(--color-peligro);
}

.form-select__error {
  margin: 0;
  font-size: var(--texto-sm);
  color: var(--color-peligro);
}
</style>
