<script setup lang="ts">
withDefaults(
  defineProps<{
    id: string;
    etiqueta: string;
    modelValue: string;
    tipo?: string;
    pista?: string;
    mensajeError?: string;
  }>(),
  { tipo: "text" },
);

defineEmits<{ "update:modelValue": [string] }>();

// Los atributos que no son props declarados (autocomplete, maxlength, …)
// deben llegar al <input>, no al <div> contenedor.
defineOptions({ inheritAttrs: false });
</script>

<template>
  <div class="form-field">
    <label :for="id" class="form-field__etiqueta">{{ etiqueta }}</label>
    <p v-if="pista" :id="`${id}-pista`" class="form-field__pista">{{ pista }}</p>
    <input
      :id="id"
      class="form-field__input"
      :type="tipo"
      :value="modelValue"
      :aria-describedby="pista ? `${id}-pista` : undefined"
      :aria-invalid="Boolean(mensajeError)"
      v-bind="$attrs"
      @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
    />
    <p v-if="mensajeError" class="form-field__error" role="alert">{{ mensajeError }}</p>
  </div>
</template>

<style scoped>
.form-field {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-xs);
}

.form-field__etiqueta {
  font-family: var(--fuente-cuerpo);
  font-weight: 600;
  font-size: var(--texto-base);
}

.form-field__pista {
  margin: 0;
  font-size: var(--texto-sm);
  color: var(--color-tinta-suave);
}

.form-field__input {
  min-height: var(--area-tactil-minima);
  padding: 0 0.75rem;
  border: 1px solid var(--color-linea);
  border-radius: var(--radio-md);
  font-family: var(--fuente-cuerpo);
  font-size: var(--texto-base);
  background: var(--color-papel);
  color: var(--color-tinta);
}

.form-field__input:focus-visible {
  outline: 2px solid var(--color-accion);
  outline-offset: 1px;
}

.form-field__error {
  margin: 0;
  font-size: var(--texto-sm);
  color: var(--color-etiqueta-alerta-texto);
}
</style>
