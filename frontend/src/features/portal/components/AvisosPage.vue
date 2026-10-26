<script setup lang="ts">
import { onMounted, reactive, ref, watch } from "vue";

import {
  abrirConversacion,
  announcementsApi,
  conversationsApi,
  iniciarConversacion,
  responderConversacion,
} from "@/features/comunicacion/api/comunicacionApi";
import ConversacionHilo from "@/features/comunicacion/components/ConversacionHilo.vue";
import { useBuzonStore } from "@/features/comunicacion/stores/buzonStore";
import { useAuthStore } from "@/features/auth/stores/authStore";
import { mensajeDelServidor } from "@/shared/api/errores";
import { usePortalStore } from "@/features/portal/stores/portalStore";
import { AppButton, CargandoBloque, EmptyState, ErrorBanner, FormField, PageHeader, TagPill } from "@/shared/components";
import type { Announcement, Conversation, ConversationDetail } from "@/shared/types/models";

const portal = usePortalStore();
const auth = useAuthStore();
const buzon = useBuzonStore();

const cargando = ref(true);
const error = ref("");
const avisos = ref<Announcement[]>([]);
const conversaciones = ref<Conversation[]>([]);

async function cargar(): Promise<void> {
  if (!portal.estudianteSeleccionadoId) return;
  cargando.value = true;
  error.value = "";
  try {
    const [avisosResp, conversacionesResp] = await Promise.all([
      announcementsApi.listar(),
      conversationsApi.listar(),
    ]);
    avisos.value = avisosResp.results;
    conversaciones.value = conversacionesResp.results;
    void buzon.actualizar();
  } catch {
    error.value = "No se pudo cargar los avisos y el buzón. Inténtalo de nuevo.";
  } finally {
    cargando.value = false;
  }
}

// RF-37: la familia escribe sobre el estudiante elegido; la conversación
// llega a los docentes de su sección y a Dirección.
const enviando = ref(false);
const errorEnvio = ref("");
const formulario = reactive({ subject: "", content: "" });

async function enviar(): Promise<void> {
  if (!portal.estudianteSeleccionadoId) return;
  enviando.value = true;
  errorEnvio.value = "";
  try {
    abierta.value = await iniciarConversacion({
      student: portal.estudianteSeleccionadoId,
      subject: formulario.subject,
      content: formulario.content,
    });
    formulario.subject = "";
    formulario.content = "";
    await cargar();
  } catch (err) {
    errorEnvio.value = mensajeDelServidor(err, "No se pudo enviar el mensaje. Inténtalo de nuevo.");
  } finally {
    enviando.value = false;
  }
}

// RF-37: abrir una conversación la marca como leída y deja responder.
const abierta = ref<ConversationDetail | null>(null);
const respondiendo = ref(false);
const errorRespuesta = ref("");
const respuesta = reactive({ texto: "" });

async function alternar(conversacion: Conversation): Promise<void> {
  respuesta.texto = "";
  errorRespuesta.value = "";
  if (abierta.value?.public_id === conversacion.public_id) {
    abierta.value = null;
    return;
  }
  try {
    abierta.value = await abrirConversacion(conversacion.public_id);
    conversaciones.value = conversaciones.value.map((c) =>
      c.public_id === conversacion.public_id ? { ...c, no_leido: false } : c,
    );
    void buzon.actualizar();
  } catch {
    error.value = "No se pudo abrir la conversación. Inténtalo de nuevo.";
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
    conversaciones.value = (await conversationsApi.listar()).results;
  } catch (err) {
    errorRespuesta.value = mensajeDelServidor(err, "No se pudo enviar la respuesta. Inténtalo de nuevo.");
  } finally {
    respondiendo.value = false;
  }
}

function fechaAviso(aviso: Announcement): string {
  return new Date(aviso.published_at).toLocaleDateString("es-GT", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

watch(() => portal.estudianteSeleccionadoId, cargar);
onMounted(cargar);
</script>

<template>
  <section class="avisos-page">
    <PageHeader titulo="Avisos" />

    <ErrorBanner v-if="error" :mensaje="error" etiqueta-accion="Reintentar" @accion="cargar" />
    <CargandoBloque v-else-if="cargando" />

    <template v-else>
      <EmptyState
        v-if="avisos.length === 0"
        titulo="No hay avisos"
        descripcion="Los avisos de la cartelera van a aparecer aquí."
      />
      <ul v-else class="avisos-page__lista">
        <li
          v-for="aviso in avisos"
          :key="aviso.public_id"
          class="avisos-page__aviso"
          :class="{ 'avisos-page__aviso--seccion': aviso.audience === 'seccion' }"
        >
          <div class="avisos-page__cabecera">
            <TagPill :variante="aviso.audience === 'seccion' ? 'hoy' : 'aviso'">
              {{ aviso.audience === "seccion" ? "Para tu sección" : "Para todos" }}
            </TagPill>
            <time class="avisos-page__fecha" :datetime="aviso.published_at">{{ fechaAviso(aviso) }}</time>
          </div>
          <h3 class="avisos-page__titulo">{{ aviso.title }}</h3>
          <p class="avisos-page__contenido">{{ aviso.content }}</p>
        </li>
      </ul>

      <h2>Buzón</h2>
      <p class="avisos-page__ayuda">
        Escríbele a la sección de tu hijo o hija. Te responde su docente o Dirección, y el centro también puede escribirte.
      </p>
      <details class="avisos-page__nuevo" :open="conversaciones.length === 0">
        <summary>Escribir un mensaje nuevo</summary>
        <ErrorBanner v-if="errorEnvio" :mensaje="errorEnvio" />
        <form class="avisos-page__formulario" @submit.prevent="enviar">
          <FormField id="subject" etiqueta="Asunto" v-model="formulario.subject" />
          <FormField id="content" etiqueta="Mensaje" multilinea v-model="formulario.content" />
          <AppButton tipo="submit" :deshabilitado="enviando || !formulario.subject || !formulario.content">
            {{ enviando ? "Enviando…" : "Enviar" }}
          </AppButton>
        </form>
      </details>

      <EmptyState
        v-if="conversaciones.length === 0"
        titulo="No hay mensajes"
        descripcion="Los mensajes que envíes o que te envíe el centro van a aparecer aquí."
      />
      <ul v-else class="avisos-page__hilos">
        <li
          v-for="conversacion in conversaciones"
          :key="conversacion.public_id"
          class="avisos-page__hilo"
          :class="{ 'avisos-page__hilo--no-leido': conversacion.no_leido }"
        >
          <button
            type="button"
            class="avisos-page__hilo-cabecera"
            :aria-expanded="abierta?.public_id === conversacion.public_id"
            @click="alternar(conversacion)"
          >
            <span class="avisos-page__resumen">
              <span class="avisos-page__asunto">{{ conversacion.subject }}</span>
              <span class="avisos-page__sobre">Sobre {{ conversacion.student_name }}</span>
            </span>
            <TagPill v-if="conversacion.no_leido" variante="aviso">Sin leer</TagPill>
          </button>
          <div v-if="abierta?.public_id === conversacion.public_id" class="avisos-page__detalle">
            <ConversacionHilo :mensajes="abierta.messages" :usuario-actual="auth.usuario?.username ?? ''" />
            <ErrorBanner v-if="errorRespuesta" :mensaje="errorRespuesta" />
            <form class="avisos-page__formulario" @submit.prevent="responder">
              <FormField id="respuesta" etiqueta="Responder" multilinea v-model="respuesta.texto" />
              <AppButton tipo="submit" :deshabilitado="respondiendo || !respuesta.texto.trim()">
                {{ respondiendo ? "Enviando…" : "Enviar respuesta" }}
              </AppButton>
            </form>
          </div>
        </li>
      </ul>
    </template>
  </section>
</template>

<style scoped>
.avisos-page {
  min-width: 0;
}

.avisos-page h2 {
  font-family: var(--fuente-titulo);
  font-size: var(--texto-md);
  margin: var(--espacio-xl) 0 var(--espacio-xs);
}

.avisos-page__ayuda {
  margin: 0 0 var(--espacio-md);
  color: var(--color-tinta-suave);
  font-size: var(--texto-sm);
}

.avisos-page__lista,
.avisos-page__hilos {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--espacio-md);
}

/* Los avisos son lo primero que se busca: tarjeta con color propio y
   franja lateral, no una línea más sobre fondo blanco. */
.avisos-page__aviso {
  padding: var(--espacio-md) var(--espacio-lg);
  background: var(--color-etiqueta-aviso-fondo);
  color: var(--color-etiqueta-aviso-texto);
  border-left: 6px solid #d9a400;
  border-radius: var(--radio-lg);
  min-width: 0;
}

.avisos-page__aviso--seccion {
  background: var(--color-etiqueta-hoy-fondo);
  color: var(--color-etiqueta-hoy-texto);
  border-left-color: var(--color-accion);
}

.avisos-page__cabecera {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--espacio-sm);
  margin-bottom: var(--espacio-xs);
}

.avisos-page__titulo {
  margin: 0 0 var(--espacio-2xs);
  font-family: var(--fuente-titulo);
  font-size: var(--texto-md);
  overflow-wrap: anywhere;
}

.avisos-page__contenido {
  margin: 0;
  color: var(--color-tinta);
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.avisos-page__fecha {
  font-size: var(--texto-sm);
  font-weight: 600;
}

.avisos-page__formulario {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-md);
  align-items: flex-start;
  margin-bottom: var(--espacio-lg);
}

.avisos-page__formulario :deep(.form-field) {
  width: 100%;
}

.avisos-page__hilo {
  min-width: 0;
}

.avisos-page__asunto {
  margin: 0 0 var(--espacio-xs);
  font-size: var(--texto-base);
  overflow-wrap: anywhere;
}

.avisos-page__nuevo {
  margin-bottom: var(--espacio-md);
  padding: var(--espacio-sm) var(--espacio-md);
  background: var(--color-papel);
  border: 1px solid var(--color-linea);
  border-radius: var(--radio-lg);
}

.avisos-page__nuevo > summary {
  min-height: var(--area-tactil-minima);
  display: flex;
  align-items: center;
  font-weight: 600;
  cursor: pointer;
}

.avisos-page__hilo {
  padding: var(--espacio-md);
  background: var(--color-papel);
  border: 1px solid var(--color-linea);
  border-radius: var(--radio-lg);
}

.avisos-page__hilo--no-leido {
  border-left: 4px solid #d9a400;
}

.avisos-page__hilo-cabecera {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--espacio-sm);
  min-height: var(--area-tactil-minima);
  padding: 0;
  background: none;
  border: none;
  text-align: left;
  font-family: var(--fuente-cuerpo);
  color: inherit;
  cursor: pointer;
}

.avisos-page__resumen {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.avisos-page__hilo-cabecera .avisos-page__asunto {
  margin: 0;
  font-weight: 700;
}

.avisos-page__hilo--no-leido .avisos-page__asunto {
  font-weight: 800;
}

.avisos-page__sobre {
  font-size: var(--texto-sm);
  color: var(--color-tinta-suave);
}

.avisos-page__detalle {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-md);
  margin-top: var(--espacio-md);
}
</style>
