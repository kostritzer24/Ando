<script setup lang="ts">
import { X } from "lucide-vue-next";
import { onBeforeUnmount, onMounted, ref, useId } from "vue";

withDefaults(defineProps<{ titulo: string; amplio?: boolean }>(), { amplio: false });
const emit = defineEmits<{ cerrar: [] }>();

const idTitulo = useId();
const dialogo = ref<HTMLElement | null>(null);
let focoAnterior: HTMLElement | null = null;

const SELECTOR_ENFOCABLE =
  'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

function enfocables(): HTMLElement[] {
  return Array.from(dialogo.value?.querySelectorAll<HTMLElement>(SELECTOR_ENFOCABLE) ?? []);
}

// Escape cierra y Tab no se escapa del diálogo (WCAG 2.1: el foco queda
// dentro de lo que el usuario está viendo mientras el diálogo está abierto).
function alPresionarTecla(evento: KeyboardEvent): void {
  if (evento.key === "Escape") {
    evento.stopPropagation();
    emit("cerrar");
    return;
  }
  if (evento.key !== "Tab") return;
  const lista = enfocables();
  if (lista.length === 0) return;
  const primero = lista[0];
  const ultimo = lista[lista.length - 1];
  if (evento.shiftKey && document.activeElement === primero) {
    evento.preventDefault();
    ultimo.focus();
  } else if (!evento.shiftKey && document.activeElement === ultimo) {
    evento.preventDefault();
    primero.focus();
  }
}

function alHacerClicEnFondo(evento: MouseEvent): void {
  if (evento.target === evento.currentTarget) {
    emit("cerrar");
  }
}

onMounted(() => {
  focoAnterior = document.activeElement as HTMLElement | null;
  document.body.classList.add("sin-desplazamiento");
  // El primer campo del formulario, no el botón de cerrar: quien abre
  // "Agregar curso" quiere escribir, no cerrar.
  const campo = dialogo.value?.querySelector<HTMLElement>(
    ".app-modal__cuerpo input, .app-modal__cuerpo select, .app-modal__cuerpo textarea, .app-modal__cuerpo button",
  );
  (campo ?? dialogo.value)?.focus();
});

onBeforeUnmount(() => {
  document.body.classList.remove("sin-desplazamiento");
  focoAnterior?.focus?.();
});
</script>

<template>
  <div class="app-modal__fondo" @click="alHacerClicEnFondo" @keydown="alPresionarTecla">
    <div
      ref="dialogo"
      class="app-modal"
      :class="{ 'app-modal--amplio': amplio }"
      role="dialog"
      aria-modal="true"
      :aria-labelledby="idTitulo"
      tabindex="-1"
    >
      <header class="app-modal__cabecera">
        <h2 :id="idTitulo" class="app-modal__titulo">{{ titulo }}</h2>
        <button type="button" class="app-modal__cerrar" aria-label="Cerrar" @click="emit('cerrar')">
          <X aria-hidden="true" />
        </button>
      </header>
      <div class="app-modal__cuerpo">
        <slot />
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Mobile-first: en el teléfono el diálogo es una hoja que sube desde
   abajo y ocupa todo el ancho (el pulgar llega a los botones); desde
   40rem es un diálogo centrado. */
.app-modal__fondo {
  position: fixed;
  inset: 0;
  z-index: var(--capa-modal);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  background: rgb(20 24 28 / 45%);
  animation: aparecer-fondo var(--transicion);
}

.app-modal {
  display: flex;
  flex-direction: column;
  width: 100%;
  max-height: 92dvh;
  background: var(--color-papel);
  border-radius: var(--radio-lg) var(--radio-lg) 0 0;
  box-shadow: var(--sombra-flotante);
  animation: subir-hoja 200ms ease-out;
}

.app-modal:focus {
  outline: none;
}

.app-modal__cabecera {
  flex: none;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--espacio-md);
  padding: var(--espacio-sm) var(--espacio-sm) var(--espacio-sm) var(--espacio-lg);
  border-bottom: 1px solid var(--color-linea);
}

.app-modal__titulo {
  font-size: var(--texto-md);
  font-weight: 700;
}

.app-modal__cerrar {
  flex: none;
  display: grid;
  place-items: center;
  width: var(--area-tactil-minima);
  height: var(--area-tactil-minima);
  background: none;
  border: none;
  border-radius: var(--radio-md);
  color: var(--color-tinta-suave);
  cursor: pointer;
}

.app-modal__cerrar:hover {
  background: var(--color-hover);
  color: var(--color-tinta);
}

.app-modal__cerrar svg {
  width: 1.25rem;
  height: 1.25rem;
}

.app-modal__cuerpo {
  overflow-y: auto;
  overscroll-behavior: contain;
  padding: var(--espacio-lg) var(--espacio-lg) calc(var(--espacio-xl) + env(safe-area-inset-bottom, 0px));
  display: flex;
  flex-direction: column;
  gap: var(--espacio-lg);
}

@media (min-width: 40rem) {
  .app-modal__fondo {
    align-items: flex-start;
    padding: 8vh var(--espacio-lg) var(--espacio-lg);
  }

  .app-modal {
    max-width: 32rem;
    max-height: 84vh;
    border-radius: var(--radio-lg);
    animation: aparecer-dialogo 160ms ease-out;
  }

  .app-modal--amplio {
    max-width: 48rem;
  }

  .app-modal__cuerpo {
    padding: var(--espacio-xl);
  }
}

@keyframes aparecer-fondo {
  from {
    opacity: 0;
  }
}

@keyframes subir-hoja {
  from {
    transform: translateY(24px);
    opacity: 0;
  }
}

@keyframes aparecer-dialogo {
  from {
    transform: scale(0.98);
    opacity: 0;
  }
}
</style>
