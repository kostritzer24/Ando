<script setup lang="ts">
import { TagPill } from "@/shared/components";
import type { Message } from "@/shared/types/models";

/**
 * Una conversación del buzón: cada mensaje en su burbuja, los
 * propios a la derecha y los de la otra parte a la izquierda, con el
 * nombre y el cargo de quien escribe (familia, docente o dirección).
 * Las palabras larguísimas se parten dentro de la burbuja en lugar de
 * ensanchar la pantalla.
 */
const props = defineProps<{
  mensajes: Message[];
  /** Nombre de usuario de quien mira, para saber qué burbujas son suyas. */
  usuarioActual: string;
}>();

// Lo propio se lee "Tú"; una familia aparece como "Encargado / Alumno".
function quien(mensaje: Message): string {
  if (mensaje.sender === props.usuarioActual) return "Tú";
  return mensaje.sender_label || mensaje.sender_name || mensaje.sender;
}

function cargo(mensaje: Message): string {
  switch (mensaje.sender_role) {
    case "Padre de familia":
      return "Familia";
    case "Dirección":
      return "Dirección";
    case "Docente":
      return "Docente";
    default:
      return mensaje.sender_role ?? "";
  }
}

function fecha(mensaje: Message): string {
  return new Date(mensaje.created_at).toLocaleString("es-GT", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
</script>

<template>
  <ol class="conversacion">
    <li
      v-for="mensaje in mensajes"
      :key="mensaje.public_id"
      class="conversacion__fila"
      :class="{ 'conversacion__fila--propia': mensaje.sender === usuarioActual }"
    >
      <article class="conversacion__burbuja">
        <header class="conversacion__encabezado">
          <strong class="conversacion__nombre">{{ quien(mensaje) }}</strong>
          <TagPill :variante="mensaje.sender_role === 'Padre de familia' ? 'hoy' : 'taller'">
            {{ cargo(mensaje) }}
          </TagPill>
        </header>
        <p class="conversacion__texto">{{ mensaje.content }}</p>
        <time class="conversacion__fecha" :datetime="mensaje.created_at">{{ fecha(mensaje) }}</time>
      </article>
    </li>
  </ol>
</template>

<style scoped>
.conversacion {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--espacio-sm);
  min-width: 0;
}

.conversacion__fila {
  display: flex;
  min-width: 0;
}

.conversacion__fila--propia {
  justify-content: flex-end;
}

.conversacion__burbuja {
  max-width: min(36rem, 92%);
  min-width: 0;
  padding: var(--espacio-sm) var(--espacio-md);
  background: var(--color-papel);
  border: 1px solid var(--color-linea);
  border-radius: var(--radio-lg);
  border-top-left-radius: var(--radio-sm);
}

.conversacion__fila--propia .conversacion__burbuja {
  background: var(--color-accion-suave);
  border-color: transparent;
  border-top-left-radius: var(--radio-lg);
  border-top-right-radius: var(--radio-sm);
}

.conversacion__encabezado {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--espacio-xs);
  margin-bottom: var(--espacio-2xs);
}

.conversacion__nombre {
  font-size: var(--texto-sm);
  overflow-wrap: anywhere;
}

.conversacion__texto {
  margin: 0;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.conversacion__fecha {
  display: block;
  margin-top: var(--espacio-xs);
  font-size: var(--texto-xs);
  color: var(--color-tinta-suave);
}
</style>
