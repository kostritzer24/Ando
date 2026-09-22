<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";

import { useAuthStore } from "@/features/auth/stores/authStore";
import { cursosApi, seccionesApi } from "@/features/catalogo/api/catalogoApi";
import { AppButton, AppModal, DataTable, EmptyState, ErrorBanner, FormSelect } from "@/shared/components";
import type { components } from "@/shared/types/api";
import type { Course, Section, TeacherAssignment } from "@/shared/types/models";

import { assignmentsApi, listarUsuariosPorRoles } from "../api/asignacionesApi";

type Usuario = components["schemas"]["User"];

const ROLES_POR_TIPO_CURSO: Record<string, string[]> = {
  academico: ["Docente", "Docente con sección a cargo"],
  taller: ["Tallerista"],
};

const auth = useAuthStore();
const puedeEditar = computed(() => auth.usuario?.role_name === "Dirección");

const asignaciones = ref<TeacherAssignment[]>([]);
const secciones = ref<Section[]>([]);
const cursos = ref<Course[]>([]);
const docentes = ref<Usuario[]>([]);
const talleristas = ref<Usuario[]>([]);
const cargando = ref(true);
const error = ref("");

const modalAbierto = ref(false);
const guardando = ref(false);
const formulario = reactive({ section: "", course: "", teacher: "" });

const seccionElegida = computed(() => secciones.value.find((s) => s.public_id === formulario.section));
const cursosDisponibles = computed(() => {
  const tipo = seccionElegida.value?.type;
  if (!tipo) return [];
  const tipoCurso = tipo === "academica" ? "academico" : "taller";
  return cursos.value.filter((c) => c.type === tipoCurso);
});
const docentesDisponibles = computed(() => {
  const tipo = seccionElegida.value?.type;
  if (!tipo) return [];
  const tipoCurso = tipo === "academica" ? "academico" : "taller";
  const roles = ROLES_POR_TIPO_CURSO[tipoCurso] ?? [];
  return [...docentes.value, ...talleristas.value].filter((u) => roles.includes(u.role_name));
});

const opcionesSeccion = computed(() =>
  secciones.value.map((s) => ({
    valor: s.public_id,
    etiqueta: `${s.grade} ${s.letter}`.trim() + (s.type === "taller" ? " (taller)" : ""),
  })),
);
const opcionesCurso = computed(() =>
  cursosDisponibles.value.map((c) => ({ valor: c.public_id, etiqueta: c.name })),
);
const opcionesDocente = computed(() =>
  docentesDisponibles.value.map((u) => ({
    valor: u.public_id,
    etiqueta: `${u.first_name} ${u.last_name}`.trim() || u.username,
  })),
);

function nombreSeccion(id: string): string {
  const s = secciones.value.find((s) => s.public_id === id);
  return s ? `${s.grade} ${s.letter}`.trim() : "—";
}
function nombreCurso(id: string): string {
  return cursos.value.find((c) => c.public_id === id)?.name ?? "—";
}
function nombreDocente(id: string): string {
  const u = [...docentes.value, ...talleristas.value].find((u) => u.public_id === id);
  return u ? `${u.first_name} ${u.last_name}`.trim() || u.username : "—";
}

async function cargar(): Promise<void> {
  cargando.value = true;
  error.value = "";
  try {
    const [asignacionesResp, seccionesResp, cursosResp, docentesResp, talleristasResp] =
      await Promise.all([
        assignmentsApi.listar(),
        seccionesApi.listar(),
        cursosApi.listar(),
        listarUsuariosPorRoles(["Docente", "Docente con sección a cargo"]),
        listarUsuariosPorRoles(["Tallerista"]),
      ]);
    asignaciones.value = asignacionesResp.results;
    secciones.value = seccionesResp.results.filter((s) => s.is_active !== false);
    cursos.value = cursosResp.results.filter((c) => c.is_active !== false);
    docentes.value = docentesResp;
    talleristas.value = talleristasResp;
  } catch {
    error.value = "No se pudo cargar la lista de asignaciones. Probá de nuevo.";
  } finally {
    cargando.value = false;
  }
}

function abrirNueva(): void {
  formulario.section = "";
  formulario.course = "";
  formulario.teacher = "";
  modalAbierto.value = true;
}

async function guardar(): Promise<void> {
  const seccion = seccionElegida.value;
  if (!seccion) return;
  guardando.value = true;
  error.value = "";
  try {
    await assignmentsApi.crear({
      teacher: formulario.teacher,
      course: formulario.course,
      section: seccion.public_id,
      cycle: seccion.cycle,
    });
    modalAbierto.value = false;
    await cargar();
  } catch {
    error.value =
      "No se pudo guardar la asignación. Puede que ese docente ya tenga otra asignación en esa sección, o que el rol no coincida con el tipo de curso.";
  } finally {
    guardando.value = false;
  }
}

async function darDeBaja(asignacion: TeacherAssignment): Promise<void> {
  if (!confirm("¿Dar de baja esta asignación?")) return;
  await assignmentsApi.darDeBaja(asignacion.public_id);
  await cargar();
}

onMounted(cargar);
</script>

<template>
  <section class="asignaciones-page">
    <header class="asignaciones-page__cabecera">
      <h1>Asignaciones de docentes y talleristas</h1>
      <AppButton v-if="puedeEditar" @click="abrirNueva">Agregar asignación</AppButton>
    </header>

    <ErrorBanner v-if="error" :mensaje="error" etiqueta-accion="Reintentar" @accion="cargar" />
    <p v-else-if="cargando">Cargando…</p>
    <EmptyState
      v-else-if="asignaciones.length === 0"
      titulo="Todavía no hay asignaciones"
      descripcion="Asigná el primer docente o tallerista a una sección."
    />

    <DataTable
      v-else
      :columnas="[
        { clave: 'teacher', etiqueta: 'Docente' },
        { clave: 'course', etiqueta: 'Curso' },
        { clave: 'section', etiqueta: 'Sección' },
      ]"
      :filas="asignaciones"
    >
      <template #celda-teacher="{ fila }">{{ nombreDocente((fila as TeacherAssignment).teacher) }}</template>
      <template #celda-course="{ fila }">{{ nombreCurso((fila as TeacherAssignment).course) }}</template>
      <template #celda-section="{ fila }">{{ nombreSeccion((fila as TeacherAssignment).section) }}</template>
      <template v-if="puedeEditar" #acciones="{ fila }">
        <button type="button" class="asignaciones-page__accion" @click="darDeBaja(fila as TeacherAssignment)">
          Dar de baja
        </button>
      </template>
    </DataTable>

    <AppModal v-if="modalAbierto" titulo="Agregar asignación" @cerrar="modalAbierto = false">
      <form class="asignaciones-page__formulario" @submit.prevent="guardar">
        <FormSelect id="section" etiqueta="Sección" :opciones="opcionesSeccion" v-model="formulario.section" />
        <FormSelect
          id="course"
          etiqueta="Curso"
          :opciones="opcionesCurso"
          v-model="formulario.course"
          :placeholder="formulario.section ? 'Elegí un curso' : 'Elegí primero una sección'"
        />
        <FormSelect
          id="teacher"
          etiqueta="Docente o tallerista"
          :opciones="opcionesDocente"
          v-model="formulario.teacher"
          :placeholder="formulario.section ? 'Elegí una persona' : 'Elegí primero una sección'"
        />
        <p class="asignaciones-page__nota">
          El curso y la persona se filtran según el tipo de la sección (académica o taller) —
          ADR-0001.
        </p>
        <AppButton tipo="submit" :deshabilitado="guardando || !formulario.section">
          {{ guardando ? "Guardando…" : "Guardar" }}
        </AppButton>
      </form>
    </AppModal>
  </section>
</template>

<style scoped>
.asignaciones-page__cabecera {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--espacio-xl);
}

.asignaciones-page__cabecera h1 {
  font-family: var(--fuente-titulo);
  font-size: var(--texto-md);
  margin: 0;
}

.asignaciones-page__accion {
  background: none;
  border: none;
  color: var(--color-accion);
  font-size: var(--texto-sm);
  font-weight: 600;
  cursor: pointer;
}

.asignaciones-page__formulario {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-lg);
}

.asignaciones-page__nota {
  color: var(--color-tinta-suave);
  font-size: var(--texto-sm);
  margin: 0;
}
</style>
