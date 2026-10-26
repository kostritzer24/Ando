<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";

import { useAuthStore } from "@/features/auth/stores/authStore";
import { mensajeDelServidor } from "@/shared/api/errores";
import {
  AppButton,
  AppModal,
  CargandoBloque,
  EmptyState,
  ErrorBanner,
  FormBuscador,
  FormField,
  PageHeader,
  TagPill,
} from "@/shared/components";
import { usePermisos } from "@/shared/permisos";
import type { Conversation, ConversationDetail, Recipient } from "@/shared/types/models";

import {
  abrirConversacion,
  buscarDestinatarios,
  conversationsApi,
  iniciarConversacion,
  responderConversacion,
} from "../api/comunicacionApi";
import { useBuzonStore } from "../stores/buzonStore";
import ConversacionHilo from "./ConversacionHilo.vue";

const auth = useAuthStore();
const buzon = useBuzonStore();
const permisos = usePermisos();
const puedeEscribir = computed(() => permisos.puedeEditar("buzon"));

const cargando = ref(true);
const error = ref("");
const conversaciones = ref<Conversation[]>([]);
const abierta = ref<ConversationDetail | null>(null);
const cargandoAbierta = ref(false);
const respondiendo = ref(false);
const errorRespuesta = ref("");
const respuesta = reactive({ texto: "" });

async function cargar(): Promise<void> {
  cargando.value = true;
  error.value = "";
  try {
    // RN-19: el servidor ya la ordena por el último mensaje.
    conversaciones.value = (await conversationsApi.listar()).results;
  } catch {
    error.value = "No se pudo cargar el buzón. Inténtalo de nuevo.";
  } finally {
    cargando.value = false;
  }
}

async function alternar(conversacion: Conversation): Promise<void> {
  respuesta.texto = "";
  errorRespuesta.value = "";
  if (abierta.value?.public_id === conversacion.public_id) {
    abierta.value = null;
    return;
  }
  cargandoAbierta.value = true;
  try {
    abierta.value = await abrirConversacion(conversacion.public_id);
    conversaciones.value = conversaciones.value.map((c) =>
      c.public_id === conversacion.public_id ? { ...c, no_leido: false } : c,
    );
    void buzon.actualizar();
  } catch {
    error.value = "No se pudo abrir la conversación. Inténtalo de nuevo.";
  } finally {
    cargandoAbierta.value = false;
  }
}

async function responder(): Promise<void> {
  if (!abierta.value) return;
  respondiendo.value = true;
  errorRespuesta.value = "";
  try {
    await responderConversacion(abierta.value.public_id, respuesta.texto);
    respuesta.texto = "";
    abierta.value = await abrirConversacion(abierta.value.public_id);
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

// RF-38: conversación nueva con un encargado.
const modalNuevo = ref(false);
const destinatarios = ref<Recipient[]>([]);
const cargandoDestinatarios = ref(false);
const enviandoNuevo = ref(false);
const errorNuevo = ref("");
const nuevo = reactive({ destinatario: "", subject: "", content: "" });

const opcionesDestinatario = computed(() =>
  destinatarios.value.map((d) => ({ valor: `${d.guardian}|${d.student}`, etiqueta: d.label })),
);

async function abrirNuevo(): Promise<void> {
  modalNuevo.value = true;
  errorNuevo.value = "";
  Object.assign(nuevo, { destinatario: "", subject: "", content: "" });
  if (destinatarios.value.length > 0) return;
  cargandoDestinatarios.value = true;
  try {
    destinatarios.value = await buscarDestinatarios();
  } catch {
    errorNuevo.value = "No se pudo cargar la lista de encargados. Inténtalo de nuevo.";
  } finally {
    cargandoDestinatarios.value = false;
  }
}

async function enviarNuevo(): Promise<void> {
  const [guardian, student] = nuevo.destinatario.split("|");
  if (!guardian || !student) return;
  enviandoNuevo.value = true;
  errorNuevo.value = "";
  try {
    const creada = await iniciarConversacion({
      guardian,
      student,
      subject: nuevo.subject,
      content: nuevo.content,
    });
    modalNuevo.value = false;
    await cargar();
    abierta.value = creada;
  } catch (e) {
    errorNuevo.value = mensajeDelServidor(e, "No se pudo enviar el mensaje. Inténtalo de nuevo.");
  } finally {
    enviandoNuevo.value = false;
  }
}

function fecha(valor: string): string {
  return new Date(valor).toLocaleString("es-GT", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

onMounted(cargar);
</script>

<template>
  <section class="buzon-page">
    <PageHeader
      titulo="Buzón"
      descripcion="Conversaciones con las familias. Las ven el encargado, los docentes de la sección, quien la inició y Dirección."
    >
      <template v-if="puedeEscribir" #acciones>
        <AppButton @click="abrirNuevo">Nuevo mensaje</AppButton>
      </template>
    </PageHeader>

    <ErrorBanner v-if="error" :mensaje="error" etiqueta-accion="Reintentar" @accion="cargar" />
    <CargandoBloque v-else-if="cargando" />

    <EmptyState
      v-else-if="conversaciones.length === 0"
      titulo="No hay conversaciones"
      descripcion="Las conversaciones con las familias van a aparecer aquí."
    />
    <ul v-else class="buzon-page__lista">
      <li
        v-for="conversacion in conversaciones"
        :key="conversacion.public_id"
        class="buzon-page__hilo"
        :class="{
          'buzon-page__hilo--abierto': abierta?.public_id === conversacion.public_id,
          'buzon-page__hilo--no-leido': conversacion.no_leido,
        }"
      >
        <button
          type="button"
          class="buzon-page__cabecera"
          :aria-expanded="abierta?.public_id === conversacion.public_id"
          @click="alternar(conversacion)"
        >
          <span class="buzon-page__resumen">
            <span class="buzon-page__asunto">{{ conversacion.subject }}</span>
            <span class="buzon-page__remitente">
              {{ conversacion.family_label }} · {{ conversacion.section_label }}
            </span>
          </span>
          <span class="buzon-page__estado">
            <TagPill v-if="conversacion.no_leido" variante="aviso">Sin leer</TagPill>
            <time class="buzon-page__fecha" :datetime="conversacion.last_message_at">
              {{ fecha(conversacion.last_message_at) }}
            </time>
          </span>
        </button>

        <div v-if="abierta?.public_id === conversacion.public_id" class="buzon-page__detalle">
          <ConversacionHilo :mensajes="abierta.messages" :usuario-actual="auth.usuario?.username ?? ''" />

          <ErrorBanner v-if="errorRespuesta" :mensaje="errorRespuesta" />
          <form v-if="puedeEscribir" class="buzon-page__formulario" @submit.prevent="responder">
            <FormField id="respuesta" etiqueta="Responder" multilinea v-model="respuesta.texto" />
            <AppButton tipo="submit" :deshabilitado="respondiendo || !respuesta.texto.trim()">
              {{ respondiendo ? "Enviando…" : "Enviar respuesta" }}
            </AppButton>
          </form>
        </div>
        <CargandoBloque
          v-else-if="cargandoAbierta && abierta === null"
          :filas="1"
          class="buzon-page__detalle"
        />
      </li>
    </ul>

    <AppModal v-if="modalNuevo" titulo="Nuevo mensaje" @cerrar="modalNuevo = false">
      <ErrorBanner v-if="errorNuevo" :mensaje="errorNuevo" />
      <CargandoBloque v-if="cargandoDestinatarios" :filas="2" />
      <form v-else class="buzon-page__formulario" @submit.prevent="enviarNuevo">
        <FormBuscador
          id="destinatario"
          etiqueta="Para (encargado / alumno)"
          placeholder="Escribe el nombre del encargado o del alumno"
          :opciones="opcionesDestinatario"
          v-model="nuevo.destinatario"
        />
        <FormField id="asunto-nuevo" etiqueta="Asunto" v-model="nuevo.subject" />
        <FormField id="contenido-nuevo" etiqueta="Mensaje" multilinea v-model="nuevo.content" />
        <AppButton
          tipo="submit"
          :deshabilitado="enviandoNuevo || !nuevo.destinatario || !nuevo.subject.trim() || !nuevo.content.trim()"
        >
          {{ enviandoNuevo ? "Enviando…" : "Enviar" }}
        </AppButton>
      </form>
    </AppModal>
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

.buzon-page__hilo--no-leido .buzon-page__asunto {
  font-weight: 800;
}

.buzon-page__hilo--no-leido {
  border-left-color: #d9a400;
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
  font-weight: 600;
  overflow-wrap: anywhere;
}

.buzon-page__remitente,
.buzon-page__fecha {
  font-size: var(--texto-sm);
  color: var(--color-tinta-suave);
  overflow-wrap: anywhere;
}

.buzon-page__estado {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: var(--espacio-2xs);
  flex: none;
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
