<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";

import { becasApi, seccionesApi } from "@/features/catalogo/api/catalogoApi";
import { AppButton, AppModal, CargandoBloque, DataTable, EmptyState, ErrorBanner, FormField, FormSelect, PageHeader } from "@/shared/components";
import { usePermisos } from "@/shared/permisos";
import type { ColumnaTabla } from "@/shared/components/DataTable.vue";
import type { Scholarship, Section, Student } from "@/shared/types/models";

import { enrollmentsApi, studentsApi } from "../api/estudiantesApi";

const permisos = usePermisos();
const puedeInscribir = computed(() => permisos.puedeEditar("estudiantes_encargados"));

const router = useRouter();

const estudiantes = ref<Student[]>([]);
const secciones = ref<Section[]>([]);
const becas = ref<Scholarship[]>([]);
const cargando = ref(true);
const error = ref("");

const modalAbierto = ref(false);
const guardando = ref(false);
const codigoRecienCreado = ref("");
const formulario = reactive({
  first_name: "",
  last_name: "",
  birth_date: "",
  address: "",
  previous_institution: "",
  section: "",
  scholarship: "",
});

// El nombre va primero: en el teléfono es el título de cada bloque.
const columnas: ColumnaTabla<Student>[] = [
  { clave: "nombre", etiqueta: "Nombre", texto: (e) => `${e.first_name} ${e.last_name}` },
  { clave: "internal_code", etiqueta: "Código" },
  { clave: "birth_date", etiqueta: "Nacimiento" },
];

const opcionesSeccion = computed(() =>
  secciones.value.map((s) => ({
    valor: s.public_id,
    etiqueta: `${s.grade} ${s.letter}`.trim() + (s.type === "taller" ? " (taller)" : ""),
  })),
);
const opcionesBeca = computed(() => [
  { valor: "", etiqueta: "Ninguna" },
  ...becas.value.map((b) => ({ valor: b.public_id, etiqueta: b.name })),
]);

async function cargar(): Promise<void> {
  cargando.value = true;
  error.value = "";
  try {
    const [estudiantesResp, seccionesResp, becasResp] = await Promise.all([
      studentsApi.listar(),
      seccionesApi.listar(),
      becasApi.listar(),
    ]);
    estudiantes.value = estudiantesResp.results;
    secciones.value = seccionesResp.results.filter((s) => s.is_active !== false);
    becas.value = becasResp.results.filter((b) => b.is_active !== false);
  } catch {
    error.value = "No se pudo cargar la lista de estudiantes. Probá de nuevo.";
  } finally {
    cargando.value = false;
  }
}

function abrirNuevo(): void {
  codigoRecienCreado.value = "";
  formulario.first_name = "";
  formulario.last_name = "";
  formulario.birth_date = "";
  formulario.address = "";
  formulario.previous_institution = "";
  formulario.section = secciones.value[0]?.public_id ?? "";
  formulario.scholarship = "";
  modalAbierto.value = true;
}

async function inscribir(): Promise<void> {
  guardando.value = true;
  error.value = "";
  try {
    const seccionElegida = secciones.value.find((s) => s.public_id === formulario.section);
    if (!seccionElegida) {
      error.value = "Elegí una sección.";
      return;
    }
    const estudiante = await studentsApi.crear({
      first_name: formulario.first_name,
      last_name: formulario.last_name,
      birth_date: formulario.birth_date,
      address: formulario.address,
      previous_institution: formulario.previous_institution,
    });
    await enrollmentsApi.crear({
      student: estudiante.public_id,
      section: seccionElegida.public_id,
      cycle: seccionElegida.cycle,
      scholarship: formulario.scholarship || null,
      enrolled_at: new Date().toISOString().slice(0, 10),
    });
    codigoRecienCreado.value = estudiante.internal_code;
    await cargar();
  } catch {
    error.value = "No se pudo inscribir al estudiante. Revisá los datos e intentá de nuevo.";
  } finally {
    guardando.value = false;
  }
}

function verExpediente(estudiante: Student): void {
  router.push(`/administrativo/estudiantes/${estudiante.public_id}`);
}

onMounted(cargar);
</script>

<template>
  <section class="estudiantes-page">
    <PageHeader titulo="Estudiantes">
      <template #acciones>
        <AppButton v-if="puedeInscribir" @click="abrirNuevo" :deshabilitado="cargando">Inscribir estudiante</AppButton>
      </template>
    </PageHeader>

    <ErrorBanner v-if="error" :mensaje="error" etiqueta-accion="Reintentar" @accion="cargar" />
    <CargandoBloque v-else-if="cargando" />
    <EmptyState
      v-else-if="estudiantes.length === 0"
      titulo="Todavía no hay estudiantes inscritos"
      descripcion="Inscribí al primer estudiante del ciclo."
    />

    <DataTable
      v-else
      :columnas="columnas"
      :filas="estudiantes"
      buscable
      placeholder-busqueda="Buscar por nombre o código"
      descripcion="Estudiantes inscritos"
    >
      <template #celda-nombre="{ fila }">{{ fila.first_name }} {{ fila.last_name }}</template>
      <template #acciones="{ fila }">
        <AppButton variante="discreto" compacto @click="verExpediente(fila)">Ver expediente</AppButton>
      </template>
    </DataTable>

    <AppModal v-if="modalAbierto" titulo="Inscribir estudiante" @cerrar="modalAbierto = false">
      <p v-if="codigoRecienCreado" class="estudiantes-page__exito">
        Estudiante inscrito con el código <strong>{{ codigoRecienCreado }}</strong
        >.
      </p>
      <form v-else class="estudiantes-page__formulario" @submit.prevent="inscribir">
        <FormField id="first_name" etiqueta="Nombres" v-model="formulario.first_name" />
        <FormField id="last_name" etiqueta="Apellidos" v-model="formulario.last_name" />
        <FormField id="birth_date" etiqueta="Fecha de nacimiento" tipo="date" v-model="formulario.birth_date" />
        <FormField id="address" etiqueta="Dirección" v-model="formulario.address" />
        <FormField
          id="previous_institution"
          etiqueta="Institución anterior"
          v-model="formulario.previous_institution"
        />
        <FormSelect id="section" etiqueta="Sección" :opciones="opcionesSeccion" v-model="formulario.section" />
        <FormSelect id="scholarship" etiqueta="Beca" :opciones="opcionesBeca" v-model="formulario.scholarship" />
        <p class="estudiantes-page__nota">
          El código interno del estudiante lo asigna el sistema — se muestra acá apenas se guarda.
        </p>
        <AppButton tipo="submit" :deshabilitado="guardando">
          {{ guardando ? "Inscribiendo…" : "Inscribir" }}
        </AppButton>
      </form>
    </AppModal>
  </section>
</template>

<style scoped>


.estudiantes-page__formulario {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-lg);
}

.estudiantes-page__nota {
  color: var(--color-tinta-suave);
  font-size: var(--texto-sm);
  margin: 0;
}

.estudiantes-page__exito {
  font-size: var(--texto-base);
}
</style>
