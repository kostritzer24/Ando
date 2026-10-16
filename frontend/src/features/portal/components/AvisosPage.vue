<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";

import { announcementsApi, messagesApi } from "@/features/comunicacion/api/comunicacionApi";
import ConversacionHilo from "@/features/comunicacion/components/ConversacionHilo.vue";
import { useAuthStore } from "@/features/auth/stores/authStore";
import { mensajeDelServidor } from "@/shared/api/errores";
import { usePortalStore } from "@/features/portal/stores/portalStore";
import { AppButton, CargandoBloque, EmptyState, ErrorBanner, FormField, PageHeader, TagPill } from "@/shared/components";
import type { Announcement, Message } from "@/shared/types/models";

const portal = usePortalStore();
const auth = useAuthStore();

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
    errorEnvio.value = mensajeDelServidor(err, "No se pudo enviar el mensaje. Inténtalo de nuevo.");
  } finally {
    enviando.value = false;
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
      <p class="avisos-page__ayuda">Escríbele a la sección de tu hijo o hija. Te responde su docente o Dirección.</p>
      <ErrorBanner v-if="errorEnvio" :mensaje="errorEnvio" />
      <form class="avisos-page__formulario" @submit.prevent="enviar">
        <FormField id="subject" etiqueta="Asunto" v-model="formulario.subject" />
        <FormField id="content" etiqueta="Mensaje" multilinea v-model="formulario.content" />
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
          <h3 class="avisos-page__asunto">{{ hilo.subject }}</h3>
          <ConversacionHilo
            :hilo="hilo"
            :respuestas="respuestasDe(hilo)"
            :usuario-actual="auth.usuario?.username ?? ''"
          />
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
</style>
