<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { useRoute } from "vue-router";

import { useAuthStore } from "@/features/auth/stores/authStore";
import { AppButton, CargandoBloque, ErrorBanner, FormField, PageHeader } from "@/shared/components";
import type { Student, StudentSensitive } from "@/shared/types/models";

import { actualizarDatosSensibles, obtenerDatosSensibles, studentsApi } from "../api/estudiantesApi";

const route = useRoute();
const publicId = route.params.publicId as string;

const auth = useAuthStore();
// docs/permisos-roles.md: "Estudiantes y encargados (datos generales)"
// es E solo para Dirección — el resto de roles que llegan a esta
// pantalla (Coordinación, Administrador, ...) la ven de solo lectura.
const puedeEditarGeneral = computed(() => auth.usuario?.role_name === "Dirección");
// "Datos sensibles" es más angosto todavía (RNF-04): Dirección edita,
// Administrador solo consulta (y esa consulta queda en AccessLog), el
// resto de roles ni siquiera debería pedirle esto al backend.
const alcanceDatosSensibles = computed<"editar" | "ver" | "ninguno">(() => {
  const rol = auth.usuario?.role_name;
  if (rol === "Dirección") return "editar";
  if (rol === "Administrador del sistema") return "ver";
  return "ninguno";
});

const estudiante = ref<Student | null>(null);
const cargando = ref(true);
const error = ref("");
const guardandoGeneral = ref(false);
const formularioGeneral = reactive({
  first_name: "",
  last_name: "",
  birth_date: "",
  address: "",
  previous_institution: "",
});

const datosSensibles = ref<StudentSensitive | null>(null);
const cargandoSensibles = ref(false);
const guardandoSensibles = ref(false);
const formularioSensible = reactive({ health_notes: "", socioeconomic_notes: "" });

async function cargar(): Promise<void> {
  cargando.value = true;
  error.value = "";
  try {
    const datos = await studentsApi.obtener(publicId);
    estudiante.value = datos;
    formularioGeneral.first_name = datos.first_name;
    formularioGeneral.last_name = datos.last_name;
    formularioGeneral.birth_date = datos.birth_date;
    formularioGeneral.address = datos.address ?? "";
    formularioGeneral.previous_institution = datos.previous_institution ?? "";
  } catch {
    error.value = "No se pudo cargar el expediente. Probá de nuevo.";
  } finally {
    cargando.value = false;
  }
}

async function guardarGeneral(): Promise<void> {
  guardandoGeneral.value = true;
  error.value = "";
  try {
    estudiante.value = await studentsApi.actualizar(publicId, { ...formularioGeneral });
  } catch {
    error.value = "No se pudo guardar el expediente. Revisá los datos e intentá de nuevo.";
  } finally {
    guardandoGeneral.value = false;
  }
}

async function cargarSensibles(): Promise<void> {
  cargandoSensibles.value = true;
  try {
    datosSensibles.value = await obtenerDatosSensibles(publicId);
    formularioSensible.health_notes = datosSensibles.value.health_notes ?? "";
    formularioSensible.socioeconomic_notes = datosSensibles.value.socioeconomic_notes ?? "";
  } finally {
    cargandoSensibles.value = false;
  }
}

async function guardarSensibles(): Promise<void> {
  guardandoSensibles.value = true;
  try {
    datosSensibles.value = await actualizarDatosSensibles(publicId, { ...formularioSensible });
  } finally {
    guardandoSensibles.value = false;
  }
}

onMounted(async () => {
  await cargar();
  if (alcanceDatosSensibles.value !== "ninguno") {
    await cargarSensibles();
  }
});
</script>

<template>
  <section class="expediente-page">
    <ErrorBanner v-if="error" :mensaje="error" etiqueta-accion="Reintentar" @accion="cargar" />
    <CargandoBloque v-else-if="cargando" />

    <template v-else-if="estudiante">
      <PageHeader
        :titulo="`${estudiante.first_name} ${estudiante.last_name}`"
        :descripcion="`Código interno: ${estudiante.internal_code}`"
        volver-a="/administrativo/estudiantes"
        etiqueta-volver="Estudiantes"
      />

      <form class="expediente-page__formulario" @submit.prevent="guardarGeneral">
        <FormField
          id="first_name"
          etiqueta="Nombres"
          v-model="formularioGeneral.first_name"
          :disabled="!puedeEditarGeneral"
        />
        <FormField
          id="last_name"
          etiqueta="Apellidos"
          v-model="formularioGeneral.last_name"
          :disabled="!puedeEditarGeneral"
        />
        <FormField
          id="birth_date"
          etiqueta="Fecha de nacimiento"
          tipo="date"
          v-model="formularioGeneral.birth_date"
          :disabled="!puedeEditarGeneral"
        />
        <FormField
          id="address"
          etiqueta="Dirección"
          v-model="formularioGeneral.address"
          :disabled="!puedeEditarGeneral"
        />
        <FormField
          id="previous_institution"
          etiqueta="Institución anterior"
          v-model="formularioGeneral.previous_institution"
          :disabled="!puedeEditarGeneral"
        />
        <AppButton v-if="puedeEditarGeneral" tipo="submit" :deshabilitado="guardandoGeneral">
          {{ guardandoGeneral ? "Guardando…" : "Guardar" }}
        </AppButton>
      </form>

      <section v-if="alcanceDatosSensibles !== 'ninguno'" class="expediente-page__sensibles">
        <h2>Datos sensibles</h2>
        <p class="expediente-page__nota">
          Salud y situación socioeconómica — acceso reservado (RNF-04). Cada consulta queda
          registrada.
        </p>
        <CargandoBloque v-if="cargandoSensibles" />
        <form v-else class="expediente-page__formulario" @submit.prevent="guardarSensibles">
          <div class="expediente-page__campo-textarea">
            <label for="health_notes">Datos de salud</label>
            <textarea
              id="health_notes"
              rows="3"
              v-model="formularioSensible.health_notes"
              :disabled="alcanceDatosSensibles !== 'editar'"
            />
          </div>
          <div class="expediente-page__campo-textarea">
            <label for="socioeconomic_notes">Datos socioeconómicos</label>
            <textarea
              id="socioeconomic_notes"
              rows="3"
              v-model="formularioSensible.socioeconomic_notes"
              :disabled="alcanceDatosSensibles !== 'editar'"
            />
          </div>
          <AppButton v-if="alcanceDatosSensibles === 'editar'" tipo="submit" :deshabilitado="guardandoSensibles">
            {{ guardandoSensibles ? "Guardando…" : "Guardar datos sensibles" }}
          </AppButton>
        </form>
      </section>
    </template>
  </section>
</template>

<style scoped>

.expediente-page__formulario {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-lg);
  max-width: 28rem;
}

.expediente-page__sensibles {
  margin-top: var(--espacio-xl);
  padding-top: var(--espacio-xl);
  border-top: 1px solid var(--color-linea);
}

.expediente-page__sensibles h2 {
  font-family: var(--fuente-titulo);
  font-size: var(--texto-base);
  margin: 0 0 var(--espacio-2xs);
}

.expediente-page__nota {
  color: var(--color-tinta-suave);
  font-size: var(--texto-sm);
  margin: 0 0 var(--espacio-lg);
}

.expediente-page__campo-textarea {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-xs);
}

.expediente-page__campo-textarea textarea {
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--color-linea);
  border-radius: var(--radio-md);
  font-family: var(--fuente-cuerpo);
  font-size: var(--texto-base);
  resize: vertical;
}
</style>
