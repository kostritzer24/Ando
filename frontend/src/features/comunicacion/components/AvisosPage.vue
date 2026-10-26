<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";

import { seccionesApi } from "@/features/catalogo/api/catalogoApi";
import { AppButton, AppModal, CargandoBloque, EmptyState, ErrorBanner, FormField, FormSelect, PageHeader } from "@/shared/components";
import { avisar } from "@/shared/composables/useAvisos";
import { confirmar } from "@/shared/composables/useConfirmar";
import { mensajeDelServidor } from "@/shared/api/errores";
import { usePermisos } from "@/shared/permisos";
import type { Announcement, Section } from "@/shared/types/models";

import { announcementsApi, seccionesParaAvisos } from "../api/comunicacionApi";

const AUDIENCIA_TODOS = "todos";
const AUDIENCIA_SECCION = "seccion";

// Publica quien edita Avisos (Dirección y docentes); cada docente edita y
// retira solo lo que publicó y Dirección cualquiera (RN-18) — eso lo dice
// el servidor en `puede_editar`. Las secciones para publicar salen de
// /announcements/target-sections/; los nombres de avisos viejos, de Datos
// maestros cuando el rol lo alcanza.
const permisos = usePermisos();
const puedePublicar = computed(() => permisos.puedeEditar("avisos"));
const veSecciones = computed(() => permisos.puedeVer("datos_maestros"));

const cargando = ref(true);
const error = ref("");
const avisos = ref<Announcement[]>([]);
const secciones = ref<Section[]>([]);
const seccionesDestino = ref<Section[]>([]);

const opcionesSeccion = computed(() =>
  seccionesDestino.value.map((s) => ({
    valor: s.public_id,
    etiqueta: `${s.grade} ${s.letter ?? ""}`.trimEnd(),
  })),
);

function nombreSeccion(publicId: string | null | undefined): string {
  const seccion = [...seccionesDestino.value, ...secciones.value].find((s) => s.public_id === publicId);
  return seccion ? `${seccion.grade} ${seccion.letter ?? ""}`.trimEnd() : "";
}

async function cargar(): Promise<void> {
  cargando.value = true;
  error.value = "";
  try {
    const [avisosResp, seccionesResp, destino] = await Promise.all([
      announcementsApi.listar(),
      veSecciones.value ? seccionesApi.listar() : Promise.resolve({ results: [] as Section[] }),
      puedePublicar.value ? seccionesParaAvisos() : Promise.resolve([] as Section[]),
    ]);
    avisos.value = avisosResp.results;
    secciones.value = seccionesResp.results.filter((s) => s.is_active !== false);
    seccionesDestino.value = destino;
  } catch {
    error.value = "No se pudo cargar la cartelera de avisos. Inténtalo de nuevo.";
  } finally {
    cargando.value = false;
  }
}

const modalAbierto = ref(false);
const editando = ref<Announcement | null>(null);
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
  editando.value = null;
  formulario.title = "";
  formulario.content = "";
  formulario.audience = AUDIENCIA_TODOS;
  formulario.target_section = "";
  formulario.expires_at = "";
  errorGuardado.value = "";
  modalAbierto.value = true;
}

function abrirEdicion(aviso: Announcement): void {
  editando.value = aviso;
  formulario.title = aviso.title;
  formulario.content = aviso.content;
  formulario.audience = aviso.audience;
  formulario.target_section = aviso.target_section ?? "";
  formulario.expires_at = aviso.expires_at ? aviso.expires_at.slice(0, 10) : "";
  errorGuardado.value = "";
  modalAbierto.value = true;
}

async function guardar(): Promise<void> {
  guardando.value = true;
  errorGuardado.value = "";
  try {
    const datos = {
      title: formulario.title,
      content: formulario.content,
      audience: formulario.audience as Announcement["audience"],
      target_section: formulario.audience === AUDIENCIA_SECCION ? formulario.target_section : null,
      expires_at: formulario.expires_at ? new Date(formulario.expires_at).toISOString() : null,
    };
    if (editando.value) {
      await announcementsApi.actualizar(editando.value.public_id, datos);
      avisar("Aviso actualizado.");
    } else {
      await announcementsApi.crear(datos);
    }
    modalAbierto.value = false;
    await cargar();
  } catch (e) {
    errorGuardado.value = mensajeDelServidor(
      e,
      "No se pudo guardar el aviso. Revisa los datos e inténtalo de nuevo.",
    );
  } finally {
    guardando.value = false;
  }
}

async function retirar(aviso: Announcement): Promise<void> {
  const confirmado = await confirmar({
    titulo: `¿Retirar el aviso "${aviso.title}"?`,
    mensaje: "Deja de verse en la cartelera de docentes y familias.",
    etiquetaConfirmar: "Retirar aviso",
    peligro: true,
  });
  if (!confirmado) return;
  try {
    await announcementsApi.darDeBaja(aviso.public_id);
    avisar("Aviso retirado de la cartelera.");
    await cargar();
  } catch {
    avisar("No se pudo retirar el aviso. Inténtalo de nuevo.", "error");
  }
}

onMounted(cargar);
</script>

<template>
  <section class="avisos-page">
    <PageHeader titulo="Cartelera de avisos" descripcion="Lo que ven docentes y familias en su portal.">
      <template #acciones>
        <AppButton v-if="puedePublicar" :deshabilitado="cargando" @click="abrirNuevo">Publicar aviso</AppButton>
      </template>
    </PageHeader>

    <ErrorBanner v-if="error" :mensaje="error" etiqueta-accion="Reintentar" @accion="cargar" />
    <CargandoBloque v-else-if="cargando" />

    <template v-else>
      <EmptyState
        v-if="avisos.length === 0"
        titulo="No hay avisos"
        descripcion="Los avisos publicados van a aparecer aquí."
      />
      <ul v-else class="avisos-page__lista">
        <li
          v-for="aviso in avisos"
          :key="aviso.public_id"
          class="avisos-page__fila"
          :class="{ 'avisos-page__fila--seccion': aviso.audience === 'seccion' }"
        >
          <div class="avisos-page__contenido">
            <p class="avisos-page__titulo">{{ aviso.title }}</p>
            <p class="avisos-page__texto">{{ aviso.content }}</p>
            <p class="avisos-page__meta">
              {{ new Date(aviso.published_at).toLocaleDateString("es-GT") }} —
              {{ aviso.audience === "todos" ? "Todos" : nombreSeccion(aviso.target_section) }} —
              {{ aviso.published_by_name }}
            </p>
          </div>
          <div v-if="aviso.puede_editar" class="avisos-page__acciones">
            <AppButton variante="discreto" compacto @click="abrirEdicion(aviso)">Editar</AppButton>
            <AppButton variante="discreto" compacto @click="retirar(aviso)">Retirar</AppButton>
          </div>
        </li>
      </ul>
    </template>

    <AppModal v-if="modalAbierto" :titulo="editando ? 'Editar aviso' : 'Publicar aviso'" @cerrar="modalAbierto = false">
      <form class="avisos-page__formulario" @submit.prevent="guardar">
        <ErrorBanner v-if="errorGuardado" :mensaje="errorGuardado" />
        <FormField id="title" etiqueta="Título" v-model="formulario.title" />
        <FormField id="content" etiqueta="Contenido" multilinea v-model="formulario.content" />
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
          {{ guardando ? "Guardando…" : editando ? "Guardar cambios" : "Publicar" }}
        </AppButton>
      </form>
    </AppModal>
  </section>
</template>

<style scoped>
.avisos-page__acciones {
  display: flex;
  flex-wrap: wrap;
  gap: var(--espacio-xs);
  flex: none;
}

.avisos-page__lista {
  list-style: none;
  margin: var(--espacio-lg) 0 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--espacio-md);
}

/* Tarjetas de color con franja lateral: la cartelera se tiene que leer de
   un vistazo, no parecer una lista más sobre fondo blanco. */
.avisos-page__fila {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--espacio-md);
  padding: var(--espacio-md) var(--espacio-lg);
  background: var(--color-etiqueta-aviso-fondo);
  border-left: 6px solid #d9a400;
  border-radius: var(--radio-lg);
}

.avisos-page__fila--seccion {
  background: var(--color-etiqueta-hoy-fondo);
  border-left-color: var(--color-accion);
}

.avisos-page__contenido {
  min-width: 0;
}

.avisos-page__titulo {
  margin: 0;
  font-weight: 700;
}

.avisos-page__texto {
  margin: var(--espacio-2xs) 0;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
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
