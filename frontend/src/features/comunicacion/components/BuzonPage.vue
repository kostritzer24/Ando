<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";

import { useAuthStore } from "@/features/auth/stores/authStore";
import { mensajeDelServidor } from "@/shared/api/errores";
import { AppButton, CargandoBloque, EmptyState, ErrorBanner, FormField, PageHeader, TagPill } from "@/shared/components";
import { usePermisos } from "@/shared/permisos";
import type { Message } from "@/shared/types/models";

import { messagesApi, responderMensaje } from "../api/comunicacionApi";
import ConversacionHilo from "./ConversacionHilo.vue";

const ETIQUETA_ESTADO: Record<string, string> = {
  enviado: "Nuevo",
  leido: "Leído",
  respondido: "Respondido",
};
const VARIANTE_ESTADO: Record<string, "aviso" | "hoy" | "taller"> = {
  enviado: "aviso",
  leido: "hoy",
  respondido: "taller",
};

const auth = useAuthStore();
const permisos = usePermisos();
const puedeResponder = computed(() => permisos.puedeEditar("buzon"));

const cargando = ref(true);
const error = ref("");
const mensajes = ref<Message[]>([]);
const hiloAbiertoId = ref("");
const respondiendo = ref(false);
const errorRespuesta = ref("");
const contenidoRespuesta = reactive({ texto: "" });

const hilos = computed(() =>
  mensajes.value
    .filter((m) => !m.original_message)
    .sort((a, b) => b.created_at.localeCompare(a.created_at)),
);

function respuestasDe(hilo: Message): Message[] {
  return mensajes.value
    .filter((m) => m.original_message === hilo.public_id)
    .sort((a, b) => a.created_at.localeCompare(b.created_at));
}

async function cargar(): Promise<void> {
  cargando.value = true;
  error.value = "";
  try {
    mensajes.value = (await messagesApi.listar()).results;
  } catch {
    error.value = "No se pudo cargar el buzón. Inténtalo de nuevo.";
  } finally {
    cargando.value = false;
  }
}

function abrirHilo(hilo: Message): void {
  hiloAbiertoId.value = hiloAbiertoId.value === hilo.public_id ? "" : hilo.public_id;
  contenidoRespuesta.texto = "";
  errorRespuesta.value = "";
}

async function responder(hilo: Message): Promise<void> {
  respondiendo.value = true;
  errorRespuesta.value = "";
  try {
    await responderMensaje(hilo.public_id, contenidoRespuesta.texto);
    contenidoRespuesta.texto = "";
    await cargar();
  } catch (e) {
    errorRespuesta.value = mensajeDelServidor(
      e,
      "No se pudo enviar la respuesta. Revisa el contenido e inténtalo de nuevo.",
    );
  } finally {
    respondiendo.value = false;
  }
}

onMounted(cargar);
</script>

<template>
  <section class="buzon-page">
    <PageHeader titulo="Buzón" descripcion="Mensajes de las familias a cada sección. Responde cualquier docente de la sección o Dirección." />

    <ErrorBanner v-if="error" :mensaje="error" etiqueta-accion="Reintentar" @accion="cargar" />
    <CargandoBloque v-else-if="cargando" />

    <EmptyState
      v-else-if="hilos.length === 0"
      titulo="No hay mensajes"
      descripcion="Los mensajes que envíen las familias van a aparecer aquí."
    />
    <ul v-else class="buzon-page__lista">
      <li
        v-for="hilo in hilos"
        :key="hilo.public_id"
        class="buzon-page__hilo"
        :class="{ 'buzon-page__hilo--abierto': hiloAbiertoId === hilo.public_id }"
      >
        <button
          type="button"
          class="buzon-page__cabecera"
          :aria-expanded="hiloAbiertoId === hilo.public_id"
          @click="abrirHilo(hilo)"
        >
          <span class="buzon-page__resumen">
            <span class="buzon-page__asunto">{{ hilo.subject }}</span>
            <span class="buzon-page__remitente">{{ hilo.sender_label || hilo.sender_name || hilo.sender }}</span>
          </span>
          <TagPill :variante="VARIANTE_ESTADO[hilo.status]">{{ ETIQUETA_ESTADO[hilo.status] }}</TagPill>
        </button>

        <div v-if="hiloAbiertoId === hilo.public_id" class="buzon-page__detalle">
          <ConversacionHilo
            :hilo="hilo"
            :respuestas="respuestasDe(hilo)"
            :usuario-actual="auth.usuario?.username ?? ''"
          />

          <ErrorBanner v-if="errorRespuesta" :mensaje="errorRespuesta" />
          <form v-if="puedeResponder" class="buzon-page__formulario" @submit.prevent="responder(hilo)">
            <FormField id="respuesta" etiqueta="Responder" multilinea v-model="contenidoRespuesta.texto" />
            <AppButton tipo="submit" :deshabilitado="respondiendo || !contenidoRespuesta.texto.trim()">
              {{ respondiendo ? "Enviando…" : "Enviar respuesta" }}
            </AppButton>
          </form>
        </div>
      </li>
    </ul>
  </section>
</template>

<style scoped>
.buzon-page {
  min-width: 0;
}

.buzon-page__lista {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--espacio-sm);
}

.buzon-page__hilo {
  background: var(--color-papel);
  border: 1px solid var(--color-linea);
  border-left: 4px solid var(--color-linea-fuerte);
  border-radius: var(--radio-lg);
  min-width: 0;
}

.buzon-page__hilo--abierto {
  border-left-color: var(--color-accion);
}

.buzon-page__cabecera {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--espacio-md);
  padding: var(--espacio-md);
  background: none;
  border: none;
  text-align: left;
  cursor: pointer;
  font-family: var(--fuente-cuerpo);
  color: inherit;
}

.buzon-page__resumen {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
  min-width: 0;
}

.buzon-page__asunto {
  font-weight: 700;
  overflow-wrap: anywhere;
}

.buzon-page__remitente {
  font-size: var(--texto-sm);
  color: var(--color-tinta-suave);
  overflow-wrap: anywhere;
}

.buzon-page__detalle {
  padding: 0 var(--espacio-md) var(--espacio-md);
  display: flex;
  flex-direction: column;
  gap: var(--espacio-md);
  min-width: 0;
}

.buzon-page__formulario {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-md);
  align-items: flex-start;
}

.buzon-page__formulario :deep(.form-field) {
  width: 100%;
}
</style>
