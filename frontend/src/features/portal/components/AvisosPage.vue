<script setup lang="ts">
import { isAxiosError } from "axios";
import { computed, onMounted, reactive, ref, watch } from "vue";

import { announcementsApi, messagesApi } from "@/features/comunicacion/api/comunicacionApi";
import { usePortalStore } from "@/features/portal/stores/portalStore";
import { AppButton, CargandoBloque, EmptyState, ErrorBanner, FormField, PageHeader } from "@/shared/components";
import type { Announcement, Message } from "@/shared/types/models";

const portal = usePortalStore();

const cargando = ref(true);
const error = ref("");
const avisos = ref<Announcement[]>([]);
const mensajes = ref<Message[]>([]);

const hilos = computed(() =>
  mensajes.value.filter((m) => !m.original_message).sort((a, b) => b.created_at.localeCompare(a.created_at)),
);
function respuestasDe(hilo: Message): Message[] {
  return mensajes.value
    .filter((m) => m.original_message === hilo.public_id)
    .sort((a, b) => a.created_at.localeCompare(b.created_at));
}

const seccionActual = computed(
  () => portal.inscripcionesDelSeleccionado.find((i) => i.section_type === "academica")?.section,
);

async function cargar(): Promise<void> {
  if (!portal.estudianteSeleccionadoId) return;
  cargando.value = true;
  error.value = "";
  try {
    const [avisosResp, mensajesResp] = await Promise.all([announcementsApi.listar(), messagesApi.listar()]);
    avisos.value = avisosResp.results;
    mensajes.value = mensajesResp.results;
  } catch {
    error.value = "No se pudo cargar los avisos y el buzón. Inténtalo de nuevo.";
  } finally {
    cargando.value = false;
  }
}

const enviando = ref(false);
const errorEnvio = ref("");
const formulario = reactive({ subject: "", content: "" });

async function enviar(): Promise<void> {
  if (!seccionActual.value) return;
  enviando.value = true;
  errorEnvio.value = "";
  try {
    await messagesApi.crear({
      section: seccionActual.value,
      subject: formulario.subject,
      content: formulario.content,
    });
    formulario.subject = "";
    formulario.content = "";
    await cargar();
  } catch (err) {
    errorEnvio.value = isAxiosError(err) && Array.isArray(err.response?.data)
      ? String(err.response.data[0])
      : "No se pudo enviar el mensaje. Inténtalo de nuevo.";
  } finally {
    enviando.value = false;
  }
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
        <li v-for="aviso in avisos" :key="aviso.public_id" class="avisos-page__aviso">
          <p class="avisos-page__titulo">{{ aviso.title }}</p>
          <p>{{ aviso.content }}</p>
          <p class="avisos-page__fecha">{{ new Date(aviso.published_at).toLocaleDateString("es-GT") }}</p>
        </li>
      </ul>

      <h2>Buzón</h2>
      <ErrorBanner v-if="errorEnvio" :mensaje="errorEnvio" />
      <form class="avisos-page__formulario" @submit.prevent="enviar">
        <FormField id="subject" etiqueta="Asunto" v-model="formulario.subject" />
        <FormField id="content" etiqueta="Mensaje" v-model="formulario.content" />
        <AppButton tipo="submit" :deshabilitado="enviando || !formulario.subject || !formulario.content">
          {{ enviando ? "Enviando…" : "Enviar" }}
        </AppButton>
      </form>

      <EmptyState
        v-if="hilos.length === 0"
        titulo="No hay mensajes"
        descripcion="Los mensajes que envíes y sus respuestas van a aparecer aquí."
      />
      <ul v-else class="avisos-page__hilos">
        <li v-for="hilo in hilos" :key="hilo.public_id" class="avisos-page__hilo">
          <p class="avisos-page__titulo">{{ hilo.subject }}</p>
          <p>{{ hilo.content }}</p>
          <div v-for="respuesta in respuestasDe(hilo)" :key="respuesta.public_id" class="avisos-page__respuesta">
            <p class="avisos-page__fecha">Respuesta:</p>
            <p>{{ respuesta.content }}</p>
          </div>
        </li>
      </ul>
    </template>
  </section>
</template>

<style scoped>

.avisos-page h2 {
  font-family: var(--fuente-titulo);
  font-size: var(--texto-base);
  margin: var(--espacio-xl) 0 var(--espacio-md);
}

.avisos-page__lista,
.avisos-page__hilos {
  list-style: none;
  margin: 0;
  padding: 0;
}

.avisos-page__aviso,
.avisos-page__hilo {
  padding: var(--espacio-md) 0;
  border-bottom: 1px solid var(--color-linea);
}

.avisos-page__titulo {
  margin: 0;
  font-weight: 700;
}

.avisos-page__fecha {
  margin: var(--espacio-2xs) 0 0;
  font-size: var(--texto-sm);
  color: var(--color-tinta-suave);
}

.avisos-page__formulario {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-md);
  align-items: flex-start;
  margin-bottom: var(--espacio-lg);
}

.avisos-page__respuesta {
  margin-top: var(--espacio-sm);
  padding: var(--espacio-sm);
  background: var(--color-fondo);
  border-radius: var(--radio-md);
}
</style>
