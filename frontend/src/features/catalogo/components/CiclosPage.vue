<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";

import { mensajeDelServidor } from "@/shared/api/errores";
import { AppButton, AppModal, CargandoBloque, DataTable, ErrorBanner, FormField, FormSelect, PageHeader, TagPill } from "@/shared/components";
import { usePermisos } from "@/shared/permisos";
import type { GradingUnit, SchoolCycle } from "@/shared/types/models";

import { ciclosApi, unidadesApi } from "../api/catalogoApi";

const permisos = usePermisos();
const puedeEditar = computed(() => permisos.puedeEditar("datos_maestros"));

const ciclos = ref<SchoolCycle[]>([]);
const cargando = ref(true);
const error = ref("");
const errorModal = ref("");

const modalCicloAbierto = ref(false);
const formularioCiclo = reactive({ year: "", start_date: "", end_date: "", status: "planificado" });
const guardandoCiclo = ref(false);

const cicloSeleccionado = ref<SchoolCycle | null>(null);
const unidades = ref<GradingUnit[]>([]);
const cargandoUnidades = ref(false);
const errorUnidades = ref("");

const modalUnidadAbierto = ref(false);
const formularioUnidad = reactive({ number: "", start_date: "", end_date: "" });
const guardandoUnidad = ref(false);

const OPCIONES_ESTADO = [
  { valor: "planificado", etiqueta: "Planificado" },
  { valor: "activo", etiqueta: "Activo" },
  { valor: "cerrado", etiqueta: "Cerrado" },
];

async function cargarCiclos(): Promise<void> {
  cargando.value = true;
  error.value = "";
  try {
    const { results } = await ciclosApi.listar();
    ciclos.value = results;
  } catch {
    error.value = "No se pudo cargar la lista de ciclos. Inténtalo de nuevo.";
  } finally {
    cargando.value = false;
  }
}

function abrirNuevoCiclo(): void {
  formularioCiclo.year = "";
  formularioCiclo.start_date = "";
  formularioCiclo.end_date = "";
  formularioCiclo.status = "planificado";
  errorModal.value = "";
  modalCicloAbierto.value = true;
}

async function guardarCiclo(): Promise<void> {
  guardandoCiclo.value = true;
  errorModal.value = "";
  try {
    await ciclosApi.crear({
      year: Number(formularioCiclo.year),
      start_date: formularioCiclo.start_date,
      end_date: formularioCiclo.end_date,
      status: formularioCiclo.status as SchoolCycle["status"],
    });
    modalCicloAbierto.value = false;
    await cargarCiclos();
  } catch (e) {
    errorModal.value = mensajeDelServidor(e, "No se pudo guardar el ciclo. Revisa los datos e inténtalo de nuevo.");
  } finally {
    guardandoCiclo.value = false;
  }
}

async function verUnidades(ciclo: SchoolCycle): Promise<void> {
  cicloSeleccionado.value = ciclo;
  cargandoUnidades.value = true;
  errorUnidades.value = "";
  try {
    const { results } = await unidadesApi(ciclo.public_id).listar();
    unidades.value = results.sort((a, b) => a.number - b.number);
  } catch {
    errorUnidades.value = "No se pudieron cargar las unidades. Inténtalo de nuevo.";
  } finally {
    cargandoUnidades.value = false;
  }
}

function abrirNuevaUnidad(): void {
  formularioUnidad.number = String(unidades.value.length + 1);
  formularioUnidad.start_date = "";
  formularioUnidad.end_date = "";
  modalUnidadAbierto.value = true;
}

async function guardarUnidad(): Promise<void> {
  if (!cicloSeleccionado.value) return;
  guardandoUnidad.value = true;
  errorUnidades.value = "";
  try {
    await unidadesApi(cicloSeleccionado.value.public_id).crear({
      number: Number(formularioUnidad.number),
      start_date: formularioUnidad.start_date,
      end_date: formularioUnidad.end_date,
    });
    modalUnidadAbierto.value = false;
    await verUnidades(cicloSeleccionado.value);
  } catch {
    errorUnidades.value =
      "No se pudo guardar la unidad. Revisa que el número y las fechas no se crucen con otra unidad.";
  } finally {
    guardandoUnidad.value = false;
  }
}

onMounted(cargarCiclos);
</script>

<template>
  <section class="ciclos-page">
    <PageHeader titulo="Ciclos escolares y unidades">
      <template #acciones>
        <AppButton v-if="puedeEditar" @click="abrirNuevoCiclo" :deshabilitado="cargando">Agregar ciclo</AppButton>
      </template>
    </PageHeader>

    <ErrorBanner v-if="error" :mensaje="error" etiqueta-accion="Reintentar" @accion="cargarCiclos" />
    <CargandoBloque v-else-if="cargando" />

    <DataTable
      v-else
      :columnas="[
        { clave: 'year', etiqueta: 'Año' },
        { clave: 'start_date', etiqueta: 'Inicio' },
        { clave: 'end_date', etiqueta: 'Cierre' },
        { clave: 'status', etiqueta: 'Estado' },
      ]"
      :filas="ciclos"
    >
      <template #celda-status="{ fila }">
        <TagPill :variante="fila.status === 'activo' ? 'taller' : fila.status === 'planificado' ? 'hoy' : 'neutro'">
          {{ OPCIONES_ESTADO.find((e) => e.valor === fila.status)?.etiqueta ?? fila.status }}
        </TagPill>
      </template>
      <template #acciones="{ fila }">
        <button type="button" class="ciclos-page__accion" @click="verUnidades(fila as SchoolCycle)">
          Ver unidades
        </button>
      </template>
    </DataTable>

    <section v-if="cicloSeleccionado" class="ciclos-page__unidades">
      <header class="ciclos-page__cabecera">
        <h2>Unidades del ciclo {{ cicloSeleccionado.year }}</h2>
        <AppButton v-if="puedeEditar" variante="secundario" @click="abrirNuevaUnidad">
          Agregar unidad
        </AppButton>
      </header>

      <ErrorBanner v-if="errorUnidades" :mensaje="errorUnidades" />
      <CargandoBloque v-else-if="cargandoUnidades" />
      <p v-else-if="unidades.length === 0" class="ciclos-page__vacio">
        Este ciclo todavía no tiene unidades.
      </p>
      <DataTable
        v-else
        :columnas="[
          { clave: 'number', etiqueta: 'Unidad' },
          { clave: 'start_date', etiqueta: 'Inicio' },
          { clave: 'end_date', etiqueta: 'Cierre' },
          { clave: 'grades_due_date', etiqueta: 'Entrega de notas' },
          { clave: 'report_card_enabled_date', etiqueta: 'Boletín habilitado' },
        ]"
        :filas="unidades"
      />
      <p class="ciclos-page__nota">
        La fecha de entrega de notas y la de habilitación del boletín las calcula el sistema; no se escriben a mano.
      </p>
    </section>

    <AppModal v-if="modalCicloAbierto" titulo="Agregar ciclo" @cerrar="modalCicloAbierto = false">
      <ErrorBanner v-if="errorModal" :mensaje="errorModal" />
      <form class="ciclos-page__formulario" @submit.prevent="guardarCiclo">
        <FormField id="year" etiqueta="Año" tipo="number" v-model="formularioCiclo.year" />
        <FormField id="start_date" etiqueta="Fecha de inicio" tipo="date" v-model="formularioCiclo.start_date" />
        <FormField id="end_date" etiqueta="Fecha de cierre" tipo="date" v-model="formularioCiclo.end_date" />
        <FormSelect
          id="status"
          etiqueta="Estado"
          :opciones="OPCIONES_ESTADO"
          v-model="formularioCiclo.status"
        />
        <AppButton tipo="submit" :deshabilitado="guardandoCiclo">
          {{ guardandoCiclo ? "Guardando…" : "Guardar" }}
        </AppButton>
      </form>
    </AppModal>

    <AppModal v-if="modalUnidadAbierto" titulo="Agregar unidad" @cerrar="modalUnidadAbierto = false">
      <form class="ciclos-page__formulario" @submit.prevent="guardarUnidad">
        <FormField id="number" etiqueta="Número de unidad" tipo="number" v-model="formularioUnidad.number" />
        <FormField
          id="unit-start"
          etiqueta="Fecha de inicio"
          tipo="date"
          v-model="formularioUnidad.start_date"
        />
        <FormField id="unit-end" etiqueta="Fecha de cierre" tipo="date" v-model="formularioUnidad.end_date" />
        <AppButton tipo="submit" :deshabilitado="guardandoUnidad">
          {{ guardandoUnidad ? "Guardando…" : "Guardar" }}
        </AppButton>
      </form>
    </AppModal>
  </section>
</template>

<style scoped>
.ciclos-page__cabecera {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--espacio-xl);
}

.ciclos-page__cabecera h2 {
  font-family: var(--fuente-titulo);
  font-size: var(--texto-md);
  margin: 0;
}

.ciclos-page__accion {
  background: none;
  border: none;
  color: var(--color-accion);
  font-size: var(--texto-sm);
  font-weight: 600;
  cursor: pointer;
}

.ciclos-page__unidades {
  margin-top: var(--espacio-xl);
  padding-top: var(--espacio-xl);
  border-top: 1px solid var(--color-linea);
}

.ciclos-page__vacio {
  color: var(--color-tinta-suave);
}

.ciclos-page__nota {
  color: var(--color-tinta-suave);
  font-size: var(--texto-sm);
  margin-top: var(--espacio-md);
}

.ciclos-page__formulario {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-lg);
}
</style>
