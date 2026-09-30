<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";

import { useAuthStore } from "@/features/auth/stores/authStore";
import { AppButton, AppModal, CargandoBloque, DataTable, EmptyState, ErrorBanner, FormField, PageHeader } from "@/shared/components";
import type { Guardian, GuardianStudentLinkRead, Student } from "@/shared/types/models";

import {
  crearUsuarioFamilia,
  desvincularEstudiante,
  guardiansApi,
  listarVinculos,
  studentsApi,
  vincularEstudiante,
} from "../api/estudiantesApi";

const auth = useAuthStore();
const puedeEditar = computed(() => auth.usuario?.role_name === "Dirección");

const encargados = ref<Guardian[]>([]);
const estudiantes = ref<Student[]>([]);
const cargando = ref(true);
const error = ref("");

const modalNuevoAbierto = ref(false);
const guardandoNuevo = ref(false);
const formularioNuevo = reactive({
  username: "",
  contrasena_temporal: "",
  first_name: "",
  last_name: "",
  phone: "",
  messaging_number: "",
  occupation: "",
});

const encargadoExpandido = ref<string | null>(null);
const vinculos = ref<GuardianStudentLinkRead[]>([]);
const cargandoVinculos = ref(false);
const formularioVinculo = reactive({ student: "", relationship: "", is_primary: false });
const guardandoVinculo = ref(false);

async function cargar(): Promise<void> {
  cargando.value = true;
  error.value = "";
  try {
    const [encargadosResp, estudiantesResp] = await Promise.all([
      guardiansApi.listar(),
      studentsApi.listar(),
    ]);
    encargados.value = encargadosResp.results;
    estudiantes.value = estudiantesResp.results;
  } catch {
    error.value = "No se pudo cargar la lista de encargados. Probá de nuevo.";
  } finally {
    cargando.value = false;
  }
}

function abrirNuevo(): void {
  formularioNuevo.username = "";
  formularioNuevo.contrasena_temporal = "";
  formularioNuevo.first_name = "";
  formularioNuevo.last_name = "";
  formularioNuevo.phone = "";
  formularioNuevo.messaging_number = "";
  formularioNuevo.occupation = "";
  modalNuevoAbierto.value = true;
}

async function guardarNuevo(): Promise<void> {
  guardandoNuevo.value = true;
  error.value = "";
  try {
    const usuario = await crearUsuarioFamilia({
      username: formularioNuevo.username,
      contrasena_temporal: formularioNuevo.contrasena_temporal,
      first_name: formularioNuevo.first_name,
      last_name: formularioNuevo.last_name,
    });
    await guardiansApi.crear({
      user: usuario.public_id,
      full_name: `${formularioNuevo.first_name} ${formularioNuevo.last_name}`.trim(),
      phone: formularioNuevo.phone,
      messaging_number: formularioNuevo.messaging_number,
      occupation: formularioNuevo.occupation,
    });
    modalNuevoAbierto.value = false;
    await cargar();
  } catch {
    error.value =
      "No se pudo crear el encargado. Confirmá que el usuario no exista ya y que la contraseña cumpla los requisitos.";
  } finally {
    guardandoNuevo.value = false;
  }
}

async function verVinculos(encargado: Guardian): Promise<void> {
  if (encargadoExpandido.value === encargado.public_id) {
    encargadoExpandido.value = null;
    return;
  }
  encargadoExpandido.value = encargado.public_id;
  cargandoVinculos.value = true;
  formularioVinculo.student = "";
  formularioVinculo.relationship = "";
  formularioVinculo.is_primary = false;
  try {
    vinculos.value = await listarVinculos(encargado.public_id);
  } finally {
    cargandoVinculos.value = false;
  }
}

async function agregarVinculo(encargado: Guardian): Promise<void> {
  guardandoVinculo.value = true;
  try {
    await vincularEstudiante(encargado.public_id, { ...formularioVinculo });
    vinculos.value = await listarVinculos(encargado.public_id);
    formularioVinculo.student = "";
    formularioVinculo.relationship = "";
    formularioVinculo.is_primary = false;
  } catch {
    error.value = "No se pudo vincular al estudiante. Puede que el vínculo ya exista.";
  } finally {
    guardandoVinculo.value = false;
  }
}

async function quitarVinculo(encargado: Guardian, vinculo: GuardianStudentLinkRead): Promise<void> {
  await desvincularEstudiante(encargado.public_id, vinculo.student_public_id);
  vinculos.value = await listarVinculos(encargado.public_id);
}

onMounted(cargar);
</script>

<template>
  <section class="encargados-page">
    <PageHeader titulo="Encargados">
      <template #acciones>
        <AppButton v-if="puedeEditar" @click="abrirNuevo" :deshabilitado="cargando">Agregar encargado</AppButton>
      </template>
    </PageHeader>

    <ErrorBanner v-if="error" :mensaje="error" etiqueta-accion="Reintentar" @accion="cargar" />
    <CargandoBloque v-else-if="cargando" />
    <EmptyState
      v-else-if="encargados.length === 0"
      titulo="Todavía no hay encargados"
      descripcion="Agregá el primer encargado."
    />

    <DataTable
      v-else
      :columnas="[
        { clave: 'full_name', etiqueta: 'Nombre completo' },
        { clave: 'phone', etiqueta: 'Teléfono' },
        { clave: 'occupation', etiqueta: 'Ocupación' },
      ]"
      :filas="encargados"
      buscable
      placeholder-busqueda="Buscar encargado"
      descripcion="Encargados"
    >
      <template #acciones="{ fila }">
        <AppButton variante="discreto" compacto @click="verVinculos(fila)">
          {{ encargadoExpandido === fila.public_id ? "Ocultar vínculos" : "Ver vínculos" }}
        </AppButton>
      </template>
    </DataTable>

    <section
      v-for="encargado in encargados.filter((e) => e.public_id === encargadoExpandido)"
      :key="encargado.public_id"
      class="encargados-page__vinculos"
    >
      <h2>Estudiantes vinculados a {{ encargado.full_name }}</h2>
      <CargandoBloque v-if="cargandoVinculos" />
      <template v-else>
        <p v-if="vinculos.length === 0" class="encargados-page__vacio">Sin vínculos todavía.</p>
        <ul v-else class="encargados-page__lista">
          <li v-for="vinculo in vinculos" :key="vinculo.public_id">
            {{ vinculo.student_name }} ({{ vinculo.student_internal_code }}) —
            {{ vinculo.relationship }}
            <span v-if="vinculo.is_primary"> · principal</span>
            <button
              v-if="puedeEditar"
              type="button"
              class="encargados-page__accion"
              @click="quitarVinculo(encargado, vinculo)"
            >
              Desvincular
            </button>
          </li>
        </ul>

        <form v-if="puedeEditar" class="encargados-page__formulario-vinculo" @submit.prevent="agregarVinculo(encargado)">
          <select v-model="formularioVinculo.student" required>
            <option value="" disabled>Elegí un estudiante</option>
            <option v-for="estudiante in estudiantes" :key="estudiante.public_id" :value="estudiante.public_id">
              {{ estudiante.first_name }} {{ estudiante.last_name }} ({{ estudiante.internal_code }})
            </option>
          </select>
          <input v-model="formularioVinculo.relationship" placeholder="Parentesco (Madre, Padre, …)" required />
          <label class="encargados-page__checkbox">
            <input type="checkbox" v-model="formularioVinculo.is_primary" />
            Principal
          </label>
          <AppButton tipo="submit" variante="secundario" :deshabilitado="guardandoVinculo">
            {{ guardandoVinculo ? "Vinculando…" : "Vincular" }}
          </AppButton>
        </form>
      </template>
    </section>

    <AppModal v-if="modalNuevoAbierto" titulo="Agregar encargado" @cerrar="modalNuevoAbierto = false">
      <form class="encargados-page__formulario" @submit.prevent="guardarNuevo">
        <FormField id="username" etiqueta="Usuario" v-model="formularioNuevo.username" />
        <FormField
          id="contrasena_temporal"
          etiqueta="Contraseña temporal"
          tipo="password"
          pista="Se le pide cambiarla al primer ingreso."
          v-model="formularioNuevo.contrasena_temporal"
        />
        <FormField id="first_name" etiqueta="Nombres" v-model="formularioNuevo.first_name" />
        <FormField id="last_name" etiqueta="Apellidos" v-model="formularioNuevo.last_name" />
        <FormField id="phone" etiqueta="Teléfono" v-model="formularioNuevo.phone" />
        <FormField
          id="messaging_number"
          etiqueta="Número de mensajería"
          v-model="formularioNuevo.messaging_number"
        />
        <FormField id="occupation" etiqueta="Ocupación" v-model="formularioNuevo.occupation" />
        <AppButton tipo="submit" :deshabilitado="guardandoNuevo">
          {{ guardandoNuevo ? "Guardando…" : "Guardar" }}
        </AppButton>
      </form>
    </AppModal>
  </section>
</template>

<style scoped>


.encargados-page__accion {
  background: none;
  border: none;
  color: var(--color-accion);
  font-size: var(--texto-sm);
  font-weight: 600;
  cursor: pointer;
}

.encargados-page__vinculos {
  margin-top: var(--espacio-xl);
  padding-top: var(--espacio-xl);
  border-top: 1px solid var(--color-linea);
}

.encargados-page__vinculos h2 {
  font-family: var(--fuente-titulo);
  font-size: var(--texto-base);
  margin: 0 0 var(--espacio-md);
}

.encargados-page__vacio {
  color: var(--color-tinta-suave);
}

.encargados-page__lista {
  list-style: none;
  padding: 0;
  margin: 0 0 var(--espacio-lg);
}

.encargados-page__lista li {
  padding: var(--espacio-sm) 0;
  border-bottom: 1px solid var(--color-linea);
  display: flex;
  align-items: center;
  gap: var(--espacio-md);
}

.encargados-page__formulario-vinculo {
  display: flex;
  align-items: center;
  gap: var(--espacio-md);
  flex-wrap: wrap;
}

.encargados-page__formulario-vinculo select,
.encargados-page__formulario-vinculo input[type="text"] {
  min-height: var(--area-tactil-minima);
  padding: 0 0.75rem;
  border: 1px solid var(--color-linea);
  border-radius: var(--radio-md);
  font-family: var(--fuente-cuerpo);
  font-size: var(--texto-base);
}

.encargados-page__checkbox {
  display: flex;
  align-items: center;
  gap: var(--espacio-xs);
  font-size: var(--texto-sm);
}

.encargados-page__formulario {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-lg);
}
</style>
