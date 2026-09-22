<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";

import { useAuthStore } from "@/features/auth/stores/authStore";
import { AppButton, AppModal, DataTable, EmptyState, ErrorBanner, FormField, FormSelect } from "@/shared/components";
import type { components } from "@/shared/types/api";
import type { SchoolCycle, Section } from "@/shared/types/models";

import { ciclosApi, listarDocentesConSeccion, seccionesApi } from "../api/catalogoApi";

type Usuario = components["schemas"]["User"];

const auth = useAuthStore();
const puedeEditar = computed(() => auth.usuario?.role_name !== "Coordinación");

const secciones = ref<Section[]>([]);
const ciclos = ref<SchoolCycle[]>([]);
const docentes = ref<Usuario[]>([]);
const cargando = ref(true);
const error = ref("");

const modalAbierto = ref(false);
const editando = ref<Section | null>(null);
const guardando = ref(false);
// HU-02: dar de baja no borra — el registro se queda en la lista con
// is_active en false, para poder reactivarlo.
const mostrarInactivas = ref(false);
const seccionesVisibles = computed(() =>
  mostrarInactivas.value ? secciones.value : secciones.value.filter((s) => s.is_active !== false),
);
const formulario = reactive({
  cycle: "",
  grade: "",
  letter: "",
  type: "academica" as Section["type"],
  homeroom_teacher: "",
});

const OPCIONES_TIPO = [
  { valor: "academica", etiqueta: "Académica" },
  { valor: "taller", etiqueta: "Taller" },
];

const opcionesCiclo = computed(() =>
  ciclos.value.map((ciclo) => ({ valor: ciclo.public_id, etiqueta: String(ciclo.year) })),
);
const opcionesDocente = computed(() =>
  docentes.value.map((docente) => ({
    valor: docente.public_id,
    etiqueta: `${docente.first_name} ${docente.last_name}`.trim() || docente.username,
  })),
);

function nombreCiclo(cicloId: string): string {
  return ciclos.value.find((c) => c.public_id === cicloId)?.year.toString() ?? "—";
}

async function cargar(): Promise<void> {
  cargando.value = true;
  error.value = "";
  try {
    const [seccionesResp, ciclosResp, docentesResp] = await Promise.all([
      seccionesApi.listar(),
      ciclosApi.listar(),
      listarDocentesConSeccion(),
    ]);
    secciones.value = seccionesResp.results;
    ciclos.value = ciclosResp.results;
    docentes.value = docentesResp;
  } catch {
    error.value = "No se pudo cargar la lista de secciones. Probá de nuevo.";
  } finally {
    cargando.value = false;
  }
}

function abrirNueva(): void {
  editando.value = null;
  formulario.cycle = ciclos.value[0]?.public_id ?? "";
  formulario.grade = "";
  formulario.letter = "";
  formulario.type = "academica";
  formulario.homeroom_teacher = "";
  modalAbierto.value = true;
}

function abrirEditar(seccion: Section): void {
  editando.value = seccion;
  formulario.cycle = seccion.cycle;
  formulario.grade = seccion.grade;
  formulario.letter = seccion.letter ?? "";
  formulario.type = seccion.type;
  formulario.homeroom_teacher = seccion.homeroom_teacher ?? "";
  modalAbierto.value = true;
}

async function guardar(): Promise<void> {
  guardando.value = true;
  error.value = "";
  const payload: Partial<Section> = {
    cycle: formulario.cycle,
    grade: formulario.grade,
    letter: formulario.letter,
    type: formulario.type,
    homeroom_teacher: formulario.type === "academica" ? formulario.homeroom_teacher || null : null,
  };
  try {
    if (editando.value) {
      await seccionesApi.actualizar(editando.value.public_id, payload);
    } else {
      await seccionesApi.crear(payload);
    }
    modalAbierto.value = false;
    await cargar();
  } catch {
    error.value = "No se pudo guardar la sección. Revisá los datos e intentá de nuevo.";
  } finally {
    guardando.value = false;
  }
}

async function darDeBaja(seccion: Section): Promise<void> {
  if (!confirm(`¿Dar de baja la sección "${seccion.grade} ${seccion.letter}"?`)) return;
  await seccionesApi.darDeBaja(seccion.public_id);
  await cargar();
}

async function reactivar(seccion: Section): Promise<void> {
  await seccionesApi.actualizar(seccion.public_id, { is_active: true });
  await cargar();
}

onMounted(cargar);
</script>

<template>
  <section class="secciones-page">
    <header class="secciones-page__cabecera">
      <h1>Secciones</h1>
      <AppButton v-if="puedeEditar" @click="abrirNueva">Agregar sección</AppButton>
    </header>

    <ErrorBanner v-if="error" :mensaje="error" etiqueta-accion="Reintentar" @accion="cargar" />
    <p v-else-if="cargando">Cargando…</p>
    <EmptyState
      v-else-if="secciones.length === 0"
      titulo="Todavía no hay secciones"
      descripcion="Agregá la primera sección del ciclo."
    />

    <template v-else>
      <label class="secciones-page__toggle-inactivas">
        <input type="checkbox" v-model="mostrarInactivas" />
        Mostrar las dadas de baja
      </label>

      <DataTable
        :columnas="[
          { clave: 'grade', etiqueta: 'Grado' },
          { clave: 'letter', etiqueta: 'Letra' },
          { clave: 'type', etiqueta: 'Tipo' },
          { clave: 'cycle', etiqueta: 'Ciclo' },
        ]"
        :filas="seccionesVisibles"
      >
        <template #celda-type="{ fila }">
          {{ (fila as Section).type === "academica" ? "Académica" : "Taller" }}
        </template>
        <template #celda-cycle="{ fila }">{{ nombreCiclo((fila as Section).cycle) }}</template>
        <template v-if="puedeEditar" #acciones="{ fila }">
          <template v-if="(fila as Section).is_active === false">
            <span class="secciones-page__etiqueta-inactivo">Dada de baja</span>
            <button type="button" class="secciones-page__accion" @click="reactivar(fila as Section)">
              Reactivar
            </button>
          </template>
          <template v-else>
            <button type="button" class="secciones-page__accion" @click="abrirEditar(fila as Section)">
              Editar
            </button>
            <button type="button" class="secciones-page__accion" @click="darDeBaja(fila as Section)">
              Dar de baja
            </button>
          </template>
        </template>
      </DataTable>
    </template>

    <AppModal
      v-if="modalAbierto"
      :titulo="editando ? 'Editar sección' : 'Agregar sección'"
      @cerrar="modalAbierto = false"
    >
      <form class="secciones-page__formulario" @submit.prevent="guardar">
        <FormSelect id="cycle" etiqueta="Ciclo escolar" :opciones="opcionesCiclo" v-model="formulario.cycle" />
        <FormField id="grade" etiqueta="Grado" pista="Por ejemplo: Primero básico" v-model="formulario.grade" />
        <FormField
          id="letter"
          etiqueta="Letra"
          pista="Dejalo vacío si el grado tiene un solo grupo"
          v-model="formulario.letter"
        />
        <FormSelect id="type" etiqueta="Tipo" :opciones="OPCIONES_TIPO" v-model="formulario.type" />
        <FormSelect
          v-if="formulario.type === 'academica'"
          id="homeroom_teacher"
          etiqueta="Maestro guía"
          :opciones="opcionesDocente"
          v-model="formulario.homeroom_teacher"
        />
        <AppButton tipo="submit" :deshabilitado="guardando">
          {{ guardando ? "Guardando…" : "Guardar" }}
        </AppButton>
      </form>
    </AppModal>
  </section>
</template>

<style scoped>
.secciones-page__cabecera {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--espacio-xl);
}

.secciones-page__cabecera h1 {
  font-family: var(--fuente-titulo);
  font-size: var(--texto-md);
  margin: 0;
}

.secciones-page__toggle-inactivas {
  display: flex;
  align-items: center;
  gap: var(--espacio-sm);
  font-size: var(--texto-sm);
  color: var(--color-tinta-suave);
  margin-bottom: var(--espacio-md);
}

.secciones-page__etiqueta-inactivo {
  font-size: var(--texto-xs);
  color: var(--color-tinta-suave);
  margin-right: var(--espacio-sm);
}

.secciones-page__accion {
  background: none;
  border: none;
  color: var(--color-accion);
  font-size: var(--texto-sm);
  font-weight: 600;
  cursor: pointer;
  padding: 0.3rem 0.5rem;
}

.secciones-page__formulario {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-lg);
}
</style>
