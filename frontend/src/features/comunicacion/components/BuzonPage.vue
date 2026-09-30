<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";

import { AppButton, CargandoBloque, EmptyState, ErrorBanner, FormField, PageHeader, TagPill } from "@/shared/components";
import type { Message } from "@/shared/types/models";

import { messagesApi, responderMensaje } from "../api/comunicacionApi";

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
    error.value = "No se pudo cargar el buzón. Probá de nuevo.";
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
  } catch {
    errorRespuesta.value = "No se pudo enviar la respuesta. Revisá el contenido e intentá de nuevo.";
  } finally {
    respondiendo.value = false;
  }
}

onMounted(cargar);
</script>

<template>
  <section class="buzon-page">
    <PageHeader titulo="Buzón" />

    <ErrorBanner v-if="error" :mensaje="error" etiqueta-accion="Reintentar" @accion="cargar" />
    <CargandoBloque v-else-if="cargando" />

    <EmptyState
      v-else-if="hilos.length === 0"
      titulo="No hay mensajes"
      descripcion="Los mensajes que envíen las familias van a aparecer acá."
    />
    <ul v-else class="buzon-page__lista">
      <li v-for="hilo in hilos" :key="hilo.public_id" class="buzon-page__hilo">
        <button type="button" class="buzon-page__cabecera" @click="abrirHilo(hilo)">
          <div>
            <p class="buzon-page__asunto">{{ hilo.subject }}</p>
            <p class="buzon-page__remitente">{{ hilo.sender }}</p>
          </div>
          <TagPill :variante="VARIANTE_ESTADO[hilo.status]">{{ ETIQUETA_ESTADO[hilo.status] }}</TagPill>
        </button>

        <div v-if="hiloAbiertoId === hilo.public_id" class="buzon-page__detalle">
          <p class="buzon-page__mensaje">{{ hilo.content }}</p>
          <div v-for="respuesta in respuestasDe(hilo)" :key="respuesta.public_id" class="buzon-page__respuesta">
            <p class="buzon-page__remitente">{{ respuesta.sender }}</p>
            <p class="buzon-page__mensaje">{{ respuesta.content }}</p>
          </div>

          <ErrorBanner v-if="errorRespuesta" :mensaje="errorRespuesta" />
          <form class="buzon-page__formulario" @submit.prevent="responder(hilo)">
            <FormField id="respuesta" etiqueta="Responder" v-model="contenidoRespuesta.texto" />
            <AppButton tipo="submit" :deshabilitado="respondiendo || !contenidoRespuesta.texto">
              {{ respondiendo ? "Enviando…" : "Enviar respuesta" }}
            </AppButton>
          </form>
        </div>
      </li>
    </ul>
  </section>
</template>

<style scoped>

.buzon-page__lista {
  list-style: none;
  margin: 0;
  padding: 0;
}

.buzon-page__hilo {
  border-bottom: 1px solid var(--color-linea);
}

.buzon-page__cabecera {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--espacio-md);
  padding: var(--espacio-md) 0;
  background: none;
  border: none;
  text-align: left;
  cursor: pointer;
  font-family: var(--fuente-cuerpo);
}

.buzon-page__asunto {
  margin: 0;
  font-weight: 600;
}

.buzon-page__remitente {
  margin: 0.1rem 0 0;
  font-size: var(--texto-sm);
  color: var(--color-tinta-suave);
}

.buzon-page__detalle {
  padding: 0 0 var(--espacio-md);
  display: flex;
  flex-direction: column;
  gap: var(--espacio-md);
}

.buzon-page__mensaje {
  margin: 0.2rem 0 0;
}

.buzon-page__respuesta {
  padding: var(--espacio-sm);
  background: var(--color-fondo);
  border-radius: var(--radio-md);
}

.buzon-page__formulario {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-md);
  align-items: flex-start;
}
</style>
