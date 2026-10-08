<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";

import { cursosApi, seccionesApi } from "@/features/catalogo/api/catalogoApi";
import { AppButton, AppModal, CargandoBloque, DataTable, EmptyState, ErrorBanner, FormSelect, PageHeader } from "@/shared/components";
import { usePermisos } from "@/shared/permisos";
import { avisar } from "@/shared/composables/useAvisos";
import { confirmar } from "@/shared/composables/useConfirmar";
import type { components } from "@/shared/types/api";
import type { Course, Section, TeacherAssignment } from "@/shared/types/models";

import { opcional } from "@/shared/api/opcional";

import { assignmentsApi, listarUsuariosPorRoles } from "../api/asignacionesApi";

type Usuario = components["schemas"]["User"];

const ROLES_POR_TIPO_CURSO: Record<string, string[]> = {
  academico: ["Docente", "Docente con sección a cargo"],
  taller: ["Tallerista"],
};

const permisos = usePermisos();
const puedeEditar = computed(() => permisos.puedeEditar("horarios_calendario"));

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
function nombreDocente(asignacion: TeacherAssignment): string {
  const u = [...docentes.value, ...talleristas.value].find((u) => u.public_id === asignacion.teacher);
  return u ? `${u.first_name} ${u.last_name}`.trim() || u.username : asignacion.teacher_name || "—";
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
        opcional(listarUsuariosPorRoles(["Docente", "Docente con sección a cargo"]), []),
        opcional(listarUsuariosPorRoles(["Tallerista"]), []),
      ]);
    asignaciones.value = asignacionesResp.results;
    secciones.value = seccionesResp.results.filter((s) => s.is_active !== false);
    cursos.value = cursosResp.results.filter((c) => c.is_active !== false);
    docentes.value = docentesResp;
    talleristas.value = talleristasResp;
  } catch {
    error.value = "No se pudo cargar la lista de asignaciones. Inténtalo de nuevo.";
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
  const confirmado = await confirmar({
    titulo: "¿Dar de baja esta asignación?",
    mensaje: "La persona deja de tener ese curso a su cargo. El historial se conserva.",
    etiquetaConfirmar: "Dar de baja",
    peligro: true,
  });
  if (!confirmado) return;
  try {
    await assignmentsApi.darDeBaja(asignacion.public_id);
    avisar("Asignación dada de baja.");
    await cargar();
  } catch {
    avisar("No se pudo dar de baja la asignación. Inténtalo de nuevo.", "error");
  }
}

onMounted(cargar);
</script>

<template>
  <section class="asignaciones-page">
    <PageHeader titulo="Asignaciones de docentes y talleristas">
      <template #acciones>
        <AppButton v-if="puedeEditar" @click="abrirNueva" :deshabilitado="cargando">Agregar asignación</AppButton>
      </template>
    </PageHeader>

    <ErrorBanner v-if="error" :mensaje="error" etiqueta-accion="Reintentar" @accion="cargar" />
    <CargandoBloque v-else-if="cargando" />
    <EmptyState
      v-else-if="asignaciones.length === 0"
      titulo="Todavía no hay asignaciones"
      descripcion="Asigna el primer docente o tallerista a una sección."
    />

    <DataTable
      v-else
      :columnas="[
        { clave: 'teacher', etiqueta: 'Docente', texto: (a) => nombreDocente(a) },
        { clave: 'course', etiqueta: 'Curso', texto: (a) => nombreCurso(a.course) },
        { clave: 'section', etiqueta: 'Sección', texto: (a) => nombreSeccion(a.section) },
      ]"
      :filas="asignaciones"
      buscable
      placeholder-busqueda="Buscar asignación"
      descripcion="Asignaciones de docentes y talleristas"
    >
      <template #celda-teacher="{ fila }">{{ nombreDocente(fila) }}</template>
      <template #celda-course="{ fila }">{{ nombreCurso(fila.course) }}</template>
      <template #celda-section="{ fila }">{{ nombreSeccion(fila.section) }}</template>
      <template v-if="puedeEditar" #acciones="{ fila }">
        <AppButton variante="discreto" compacto @click="darDeBaja(fila)">Dar de baja</AppButton>
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
          :placeholder="formulario.section ? 'Elige un curso' : 'Elige primero una sección'"
        />
        <FormSelect
          id="teacher"
          etiqueta="Docente o tallerista"
          :opciones="opcionesDocente"
          v-model="formulario.teacher"
          :placeholder="formulario.section ? 'Elige una persona' : 'Elige primero una sección'"
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
