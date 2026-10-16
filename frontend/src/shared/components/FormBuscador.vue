<script setup lang="ts">
import { computed, ref, watch } from "vue";

/**
 * Selector con búsqueda: se escribe parte del nombre y la lista se acota
 * mientras tanto. Sustituye al <select> cuando las opciones son decenas
 * (estudiantes, docentes, secciones) y la lista desplegable se hace
 * inmanejable. Mismo contrato que FormSelect: `v-model` lleva el valor
 * de la opción elegida.
 */
const props = withDefaults(
  defineProps<{
    id: string;
    etiqueta: string;
    modelValue: string;
    opciones: { valor: string; etiqueta: string }[];
    placeholder?: string;
    mensajeError?: string;
  }>(),
  { placeholder: "Escribe para buscar" },
);

const emit = defineEmits<{ "update:modelValue": [string] }>();

const MAXIMO_VISIBLE = 50;

const abierto = ref(false);
const texto = ref("");
const activa = ref(0);

function sinTildes(valor: string): string {
  return valor.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
}

const etiquetaElegida = computed(
  () => props.opciones.find((o) => o.valor === props.modelValue)?.etiqueta ?? "",
);

// Cuando no se está escribiendo, el campo muestra la opción elegida.
watch(
  [etiquetaElegida, abierto],
  () => {
    if (!abierto.value) texto.value = etiquetaElegida.value;
  },
  { immediate: true },
);

const coincidencias = computed(() => {
  const termino = sinTildes(texto.value.trim());
  // Con el texto igual a la opción elegida se muestran todas: quien abre
  // el campo para cambiar la elección no debería ver una lista de uno.
  const buscando = termino && sinTildes(etiquetaElegida.value) !== termino;
  return props.opciones.filter((o) => !buscando || sinTildes(o.etiqueta).includes(termino));
});
const visibles = computed(() => coincidencias.value.slice(0, MAXIMO_VISIBLE));

watch(visibles, () => {
  activa.value = 0;
});

function abrir(): void {
  abierto.value = true;
}

function elegir(opcion: { valor: string; etiqueta: string }): void {
  emit("update:modelValue", opcion.valor);
  texto.value = opcion.etiqueta;
  abierto.value = false;
}

function cerrar(): void {
  abierto.value = false;
  texto.value = etiquetaElegida.value;
}

function alTeclear(evento: KeyboardEvent): void {
  if (evento.key === "ArrowDown") {
    evento.preventDefault();
    abierto.value = true;
    activa.value = Math.min(activa.value + 1, visibles.value.length - 1);
  } else if (evento.key === "ArrowUp") {
    evento.preventDefault();
    activa.value = Math.max(activa.value - 1, 0);
  } else if (evento.key === "Enter" && abierto.value) {
    evento.preventDefault();
    const opcion = visibles.value[activa.value];
    if (opcion) elegir(opcion);
  } else if (evento.key === "Escape") {
    cerrar();
  }
}

// El clic en una opción llega después del blur del input: se difiere el
// cierre para no perder ese clic.
function alSalir(): void {
  window.setTimeout(cerrar, 120);
}
</script>

<template>
  <div class="form-buscador">
    <label :for="id" class="form-buscador__etiqueta">{{ etiqueta }}</label>
    <input
      :id="id"
      v-model="texto"
      class="form-buscador__input"
      type="text"
      role="combobox"
      autocomplete="off"
      :placeholder="placeholder"
      :aria-expanded="abierto"
      :aria-controls="`${id}-lista`"
      :aria-activedescendant="abierto && visibles[activa] ? `${id}-op-${activa}` : undefined"
      :aria-invalid="Boolean(mensajeError)"
      @focus="abrir"
      @input="abrir"
      @keydown="alTeclear"
      @blur="alSalir"
    />
    <ul v-if="abierto" :id="`${id}-lista`" class="form-buscador__lista" role="listbox">
      <li
        v-for="(opcion, indice) in visibles"
        :id="`${id}-op-${indice}`"
        :key="opcion.valor"
        class="form-buscador__opcion"
        :class="{
          'form-buscador__opcion--activa': indice === activa,
          'form-buscador__opcion--elegida': opcion.valor === modelValue,
        }"
        role="option"
        :aria-selected="opcion.valor === modelValue"
        @mousedown.prevent="elegir(opcion)"
      >
        {{ opcion.etiqueta }}
      </li>
      <li v-if="visibles.length === 0" class="form-buscador__vacio">Sin coincidencias</li>
      <li v-else-if="coincidencias.length > visibles.length" class="form-buscador__vacio">
        Hay {{ coincidencias.length - visibles.length }} más: escribe para acotar.
      </li>
    </ul>
    <p v-if="mensajeError" class="form-buscador__error" role="alert">{{ mensajeError }}</p>
  </div>
</template>

<style scoped>
.form-buscador {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: var(--espacio-xs);
  min-width: 0;
}

.form-buscador__etiqueta {
  font-family: var(--fuente-cuerpo);
  font-weight: 600;
  font-size: var(--texto-sm);
}

.form-buscador__input {
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

.form-buscador__input:focus-visible {
  outline: 2px solid var(--color-accion);
  outline-offset: 1px;
  border-color: var(--color-accion);
}

.form-buscador__input[aria-invalid="true"] {
  border-color: var(--color-peligro);
}

.form-buscador__lista {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  z-index: 20;
  max-height: 15rem;
  margin: 2px 0 0;
  padding: var(--espacio-2xs);
  overflow-y: auto;
  list-style: none;
  background: var(--color-papel);
  border: 1px solid var(--color-borde-campo);
  border-radius: var(--radio-md);
  box-shadow: 0 8px 24px rgb(0 0 0 / 0.12);
}

.form-buscador__opcion {
  padding: var(--espacio-xs) var(--espacio-sm);
  border-radius: var(--radio-sm, 6px);
  cursor: pointer;
  overflow-wrap: anywhere;
}

.form-buscador__opcion--activa {
  background: var(--color-fondo-suave, rgb(0 0 0 / 0.06));
}

.form-buscador__opcion--elegida {
  font-weight: 700;
}

.form-buscador__vacio {
  padding: var(--espacio-xs) var(--espacio-sm);
  color: var(--color-tinta-suave);
  font-size: var(--texto-sm);
}

.form-buscador__error {
  margin: 0;
  font-size: var(--texto-sm);
  color: var(--color-peligro);
}
</style>
