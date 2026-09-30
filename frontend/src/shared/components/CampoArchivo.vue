<script setup lang="ts">
import { Paperclip } from "lucide-vue-next";
import { ref } from "vue";

withDefaults(
  defineProps<{
    id: string;
    etiqueta: string;
    accept?: string;
    pista?: string;
  }>(),
  { accept: undefined, pista: undefined },
);

const emit = defineEmits<{ elegir: [File | null] }>();
const nombre = ref("");

function alCambiar(evento: Event): void {
  const archivo = (evento.target as HTMLInputElement).files?.[0] ?? null;
  nombre.value = archivo?.name ?? "";
  emit("elegir", archivo);
}
</script>

<template>
  <!-- El <input type="file"> nativo muestra "Choose File / No file chosen"
       en el idioma del navegador, no del sistema, y no se le puede dar
       estilo. Acá el input queda accesible pero invisible, y la etiqueta
       hace de botón. -->
  <div class="campo-archivo">
    <span class="campo-archivo__etiqueta">{{ etiqueta }}</span>
    <p v-if="pista" :id="`${id}-pista`" class="campo-archivo__pista">{{ pista }}</p>
    <div class="campo-archivo__control">
      <input
        :id="id"
        type="file"
        class="campo-archivo__input"
        :accept="accept"
        :aria-describedby="pista ? `${id}-pista` : undefined"
        @change="alCambiar"
      />
      <label :for="id" class="campo-archivo__boton">
        <Paperclip aria-hidden="true" />
        Elegir archivo
      </label>
      <span class="campo-archivo__nombre" :class="{ 'campo-archivo__nombre--vacio': !nombre }">
        {{ nombre || "Ningún archivo elegido" }}
      </span>
    </div>
  </div>
</template>

<style scoped>
.campo-archivo {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-xs);
}

.campo-archivo__etiqueta {
  font-size: var(--texto-sm);
  font-weight: 600;
}

.campo-archivo__pista {
  margin: 0;
  font-size: var(--texto-sm);
  color: var(--color-tinta-suave);
}

.campo-archivo__control {
  display: flex;
  align-items: center;
  gap: var(--espacio-md);
  min-height: var(--area-tactil-minima);
  padding: var(--espacio-2xs) var(--espacio-md) var(--espacio-2xs) var(--espacio-2xs);
  border: 1px dashed var(--color-borde-campo);
  border-radius: var(--radio-md);
  background: var(--color-papel);
}

.campo-archivo__input {
  position: absolute;
  width: 1px;
  height: 1px;
  opacity: 0;
  pointer-events: none;
}

.campo-archivo__boton {
  flex: none;
  display: inline-flex;
  align-items: center;
  gap: var(--espacio-xs);
  min-height: 2.5rem;
  padding: 0 var(--espacio-md);
  border-radius: var(--radio-sm);
  background: var(--color-accion-suave);
  color: var(--color-accion);
  font-size: var(--texto-sm);
  font-weight: 600;
  cursor: pointer;
}

.campo-archivo__boton:hover {
  background: var(--color-etiqueta-hoy-fondo);
}

.campo-archivo__boton svg {
  width: 1rem;
  height: 1rem;
}

.campo-archivo__input:focus-visible + .campo-archivo__boton {
  outline: 2px solid var(--color-accion);
  outline-offset: 2px;
}

.campo-archivo__nombre {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: var(--texto-sm);
}

.campo-archivo__nombre--vacio {
  color: var(--color-tinta-suave);
}
</style>
