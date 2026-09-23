<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";

import { seccionesApi } from "@/features/catalogo/api/catalogoApi";
import { useAuthStore } from "@/features/auth/stores/authStore";
import { AppButton, AppModal, EmptyState, ErrorBanner, FormField, FormSelect } from "@/shared/components";
import type { Announcement, Section } from "@/shared/types/models";

import { announcementsApi } from "../api/comunicacionApi";

const AUDIENCIA_TODOS = "todos";
const AUDIENCIA_SECCION = "seccion";

const auth = useAuthStore();
const esDireccion = computed(() => auth.usuario?.role_name === "Dirección");

const cargando = ref(true);
const error = ref("");
const avisos = ref<Announcement[]>([]);
const secciones = ref<Section[]>([]);

const opcionesSeccion = computed(() =>
  secciones.value.map((s) => ({ valor: s.public_id, etiqueta: `${s.grade} ${s.letter ?? ""}`.trimEnd() })),
);

function nombreSeccion(publicId: string | null | undefined): string {
  const seccion = secciones.value.find((s) => s.public_id === publicId);
  return seccion ? `${seccion.grade} ${seccion.letter ?? ""}`.trimEnd() : "";
}

async function cargar(): Promise<void> {
  cargando.value = true;
  error.value = "";
  try {
    const [avisosResp, seccionesResp] = await Promise.all([
      announcementsApi.listar(),
      esDireccion.value ? seccionesApi.listar() : Promise.resolve({ results: [] as Section[] }),
    ]);
    avisos.value = avisosResp.results;
    secciones.value = seccionesResp.results;
  } catch {
    error.value = "No se pudo cargar la cartelera de avisos. Probá de nuevo.";
  } finally {
    cargando.value = false;
  }
}

const modalAbierto = ref(false);
const guardando = ref(false);
const errorGuardado = ref("");
const formulario = reactive({
  title: "",
  content: "",
  audience: AUDIENCIA_TODOS,
  target_section: "",
  expires_at: "",
});

function abrirNuevo(): void {
  formulario.title = "";
  formulario.content = "";
  formulario.audience = AUDIENCIA_TODOS;
  formulario.target_section = "";
  formulario.expires_at = "";
  errorGuardado.value = "";
  modalAbierto.value = true;
}

async function guardar(): Promise<void> {
  guardando.value = true;
  errorGuardado.value = "";
  try {
    await announcementsApi.crear({
      title: formulario.title,
      content: formulario.content,
      audience: formulario.audience as Announcement["audience"],
      target_section: formulario.audience === AUDIENCIA_SECCION ? formulario.target_section : null,
      expires_at: formulario.expires_at ? new Date(formulario.expires_at).toISOString() : null,
    });
    modalAbierto.value = false;
    await cargar();
  } catch {
    errorGuardado.value = "No se pudo publicar el aviso. Revisá los datos e intentá de nuevo.";
  } finally {
    guardando.value = false;
  }
}

async function retirar(aviso: Announcement): Promise<void> {
  await announcementsApi.darDeBaja(aviso.public_id);
  await cargar();
}

onMounted(cargar);
</script>

<template>
  <section class="avisos-page">
    <h1>Cartelera de avisos</h1>

    <ErrorBanner v-if="error" :mensaje="error" etiqueta-accion="Reintentar" @accion="cargar" />
    <p v-else-if="cargando">Cargando…</p>

    <template v-else>
      <AppButton v-if="esDireccion" @click="abrirNuevo">Publicar aviso</AppButton>

      <EmptyState
        v-if="avisos.length === 0"
        titulo="No hay avisos"
        descripcion="Los avisos publicados van a aparecer acá."
      />
      <ul v-else class="avisos-page__lista">
        <li v-for="aviso in avisos" :key="aviso.public_id" class="avisos-page__fila">
          <div class="avisos-page__contenido">
            <p class="avisos-page__titulo">{{ aviso.title }}</p>
            <p class="avisos-page__texto">{{ aviso.content }}</p>
            <p class="avisos-page__meta">
              {{ new Date(aviso.published_at).toLocaleDateString("es-GT") }} —
              {{ aviso.audience === "todos" ? "Todos" : nombreSeccion(aviso.target_section) }}
            </p>
          </div>
          <button v-if="esDireccion" type="button" class="avisos-page__accion" @click="retirar(aviso)">
            Retirar
          </button>
        </li>
      </ul>
    </template>

    <AppModal v-if="modalAbierto" titulo="Publicar aviso" @cerrar="modalAbierto = false">
      <form class="avisos-page__formulario" @submit.prevent="guardar">
        <ErrorBanner v-if="errorGuardado" :mensaje="errorGuardado" />
        <FormField id="title" etiqueta="Título" v-model="formulario.title" />
        <FormField id="content" etiqueta="Contenido" v-model="formulario.content" />
        <FormSelect
          id="audience"
          etiqueta="Destinatario"
          :opciones="[
            { valor: AUDIENCIA_TODOS, etiqueta: 'Todos' },
            { valor: AUDIENCIA_SECCION, etiqueta: 'Una sección' },
          ]"
          v-model="formulario.audience"
        />
        <FormSelect
          v-if="formulario.audience === AUDIENCIA_SECCION"
          id="target_section"
          etiqueta="Sección"
          :opciones="opcionesSeccion"
          v-model="formulario.target_section"
        />
        <FormField
          id="expires_at"
          etiqueta="Fecha de vencimiento (opcional)"
          tipo="date"
          v-model="formulario.expires_at"
        />
        <AppButton tipo="submit" :deshabilitado="guardando">
          {{ guardando ? "Publicando…" : "Publicar" }}
        </AppButton>
      </form>
    </AppModal>
  </section>
</template>

<style scoped>
.avisos-page h1 {
  font-family: var(--fuente-titulo);
  font-size: var(--texto-md);
  margin: 0 0 var(--espacio-lg);
}

.avisos-page__lista {
  list-style: none;
  margin: var(--espacio-lg) 0 0;
  padding: 0;
}

.avisos-page__fila {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--espacio-md);
  padding: var(--espacio-md) 0;
  border-bottom: 1px solid var(--color-linea);
}

.avisos-page__titulo {
  margin: 0;
  font-weight: 700;
}

.avisos-page__texto {
  margin: var(--espacio-2xs) 0;
}

.avisos-page__meta {
  margin: 0;
  font-size: var(--texto-sm);
  color: var(--color-tinta-suave);
}

.avisos-page__accion {
  flex: none;
  background: none;
  border: none;
  color: var(--color-accion);
  font-size: var(--texto-sm);
  font-weight: 600;
  cursor: pointer;
  padding: 0.3rem 0.5rem;
}

.avisos-page__formulario {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-lg);
}
</style>
