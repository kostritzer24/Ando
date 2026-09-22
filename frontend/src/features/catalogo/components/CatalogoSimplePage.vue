<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";

import { useAuthStore } from "@/features/auth/stores/authStore";
import { AppButton, AppModal, DataTable, EmptyState, ErrorBanner, FormField, FormSelect } from "@/shared/components";
import type { Registro, RecursoGenerico } from "@/shared/api/resource";

import type { CatalogoConfig } from "../config/campos";

const props = defineProps<{ config: CatalogoConfig; recurso: RecursoGenerico }>();

// docs/permisos-roles.md: "Datos maestros" es E para Dirección y
// Administrador, V para Coordinación. El backend es quien de verdad lo
// exige (PermisoPorArea) — esto solo evita mostrarle a Coordinación
// botones que van a terminar en 403.
const auth = useAuthStore();
const puedeEditar = computed(() => auth.usuario?.role_name !== "Coordinación");

const registros = ref<Registro[]>([]);
const cargando = ref(true);
const error = ref("");
const modalAbierto = ref(false);
const editando = ref<Registro | null>(null);
const formulario = reactive<Record<string, unknown>>({});
const guardando = ref(false);
// HU-02: nada se borra de verdad, "dar de baja" solo pone is_active en
// false — el registro se queda en la lista (así se puede reactivar), así
// que por defecto se esconden los dados de baja para no saturar la vista
// del día a día, con la opción de mostrarlos.
const mostrarInactivos = ref(false);

const filasVisibles = computed(() =>
  mostrarInactivos.value ? registros.value : registros.value.filter((r) => r.is_active !== false),
);

async function cargar(): Promise<void> {
  cargando.value = true;
  error.value = "";
  try {
    const { results } = await props.recurso.listar();
    registros.value = results;
  } catch {
    error.value = "No se pudo cargar la lista. Probá de nuevo.";
  } finally {
    cargando.value = false;
  }
}

function abrirNuevo(): void {
  editando.value = null;
  for (const campo of props.config.campos) {
    formulario[campo.clave] = campo.tipo === "booleano" ? false : "";
  }
  modalAbierto.value = true;
}

function abrirEditar(registro: Registro): void {
  editando.value = registro;
  for (const campo of props.config.campos) {
    formulario[campo.clave] = registro[campo.clave] ?? (campo.tipo === "booleano" ? false : "");
  }
  modalAbierto.value = true;
}

async function guardar(): Promise<void> {
  guardando.value = true;
  error.value = "";
  try {
    if (editando.value) {
      await props.recurso.actualizar(editando.value.public_id, { ...formulario });
    } else {
      await props.recurso.crear({ ...formulario });
    }
    modalAbierto.value = false;
    await cargar();
  } catch {
    error.value = "No se pudo guardar. Revisá los datos e intentá de nuevo.";
  } finally {
    guardando.value = false;
  }
}

async function darDeBaja(registro: Registro): Promise<void> {
  if (!confirm(`¿Dar de baja "${registro.name ?? registro.code ?? registro.public_id}"?`)) {
    return;
  }
  await props.recurso.darDeBaja(registro.public_id);
  await cargar();
}

async function reactivar(registro: Registro): Promise<void> {
  await props.recurso.actualizar(registro.public_id, { is_active: true });
  await cargar();
}

onMounted(cargar);
</script>

<template>
  <section class="catalogo-simple">
    <header class="catalogo-simple__cabecera">
      <h1>{{ config.titulo }}</h1>
      <AppButton v-if="puedeEditar" @click="abrirNuevo">Agregar {{ config.tituloSingular }}</AppButton>
    </header>

    <ErrorBanner v-if="error" :mensaje="error" etiqueta-accion="Reintentar" @accion="cargar" />

    <p v-else-if="cargando">Cargando…</p>

    <EmptyState
      v-else-if="registros.length === 0"
      titulo="Todavía no hay nada acá"
      :descripcion="`Agregá el primer ${config.tituloSingular} del catálogo.`"
    />

    <template v-else>
      <label class="catalogo-simple__toggle-inactivos">
        <input type="checkbox" v-model="mostrarInactivos" />
        Mostrar los dados de baja
      </label>

      <DataTable :columnas="config.columnas" :filas="filasVisibles">
        <template v-for="columna in config.columnas" :key="columna.clave" #[`celda-${columna.clave}`]="{ fila }">
          <template v-if="typeof fila[columna.clave] === 'boolean'">{{ fila[columna.clave] ? "Sí" : "No" }}</template>
          <template v-else>{{ fila[columna.clave] }}</template>
        </template>
        <template v-if="puedeEditar" #acciones="{ fila }">
          <span v-if="(fila as Registro).is_active === false" class="catalogo-simple__etiqueta-inactivo">
            Dado de baja
          </span>
          <button
            v-if="(fila as Registro).is_active === false"
            type="button"
            class="catalogo-simple__accion"
            @click="reactivar(fila as Registro)"
          >
            Reactivar
          </button>
          <template v-else>
            <button type="button" class="catalogo-simple__accion" @click="abrirEditar(fila as Registro)">
              Editar
            </button>
            <button type="button" class="catalogo-simple__accion" @click="darDeBaja(fila as Registro)">
              Dar de baja
            </button>
          </template>
        </template>
      </DataTable>
    </template>

    <AppModal
      v-if="modalAbierto"
      :titulo="editando ? `Editar ${config.tituloSingular}` : `Agregar ${config.tituloSingular}`"
      @cerrar="modalAbierto = false"
    >
      <form class="catalogo-simple__formulario" @submit.prevent="guardar">
        <template v-for="campo in config.campos" :key="campo.clave">
          <FormSelect
            v-if="campo.tipo === 'select'"
            :id="campo.clave"
            :etiqueta="campo.etiqueta"
            :opciones="campo.opciones ?? []"
            :model-value="String(formulario[campo.clave] ?? '')"
            @update:model-value="(valor) => (formulario[campo.clave] = valor)"
          />
          <label v-else-if="campo.tipo === 'booleano'" class="catalogo-simple__checkbox">
            <input
              type="checkbox"
              :checked="Boolean(formulario[campo.clave])"
              @change="(evento) => (formulario[campo.clave] = (evento.target as HTMLInputElement).checked)"
            />
            {{ campo.etiqueta }}
          </label>
          <div v-else-if="campo.tipo === 'textarea'" class="catalogo-simple__textarea">
            <label :for="campo.clave">{{ campo.etiqueta }}</label>
            <textarea
              :id="campo.clave"
              rows="3"
              :value="String(formulario[campo.clave] ?? '')"
              @input="(evento) => (formulario[campo.clave] = (evento.target as HTMLTextAreaElement).value)"
            />
          </div>
          <FormField
            v-else
            :id="campo.clave"
            :etiqueta="campo.etiqueta"
            :pista="campo.pista"
            :model-value="String(formulario[campo.clave] ?? '')"
            @update:model-value="(valor) => (formulario[campo.clave] = valor)"
          />
        </template>
        <AppButton tipo="submit" :deshabilitado="guardando">
          {{ guardando ? "Guardando…" : "Guardar" }}
        </AppButton>
      </form>
    </AppModal>
  </section>
</template>

<style scoped>
.catalogo-simple__cabecera {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--espacio-xl);
}

.catalogo-simple__cabecera h1 {
  font-family: var(--fuente-titulo);
  font-size: var(--texto-md);
  margin: 0;
}

.catalogo-simple__toggle-inactivos {
  display: flex;
  align-items: center;
  gap: var(--espacio-sm);
  font-size: var(--texto-sm);
  color: var(--color-tinta-suave);
  margin-bottom: var(--espacio-md);
}

.catalogo-simple__etiqueta-inactivo {
  font-size: var(--texto-xs);
  color: var(--color-tinta-suave);
  margin-right: var(--espacio-sm);
}

.catalogo-simple__accion {
  background: none;
  border: none;
  color: var(--color-accion);
  font-size: var(--texto-sm);
  font-weight: 600;
  cursor: pointer;
  padding: 0.3rem 0.5rem;
}

.catalogo-simple__formulario {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-lg);
}

.catalogo-simple__checkbox {
  display: flex;
  align-items: center;
  gap: var(--espacio-sm);
  font-size: var(--texto-base);
}

.catalogo-simple__textarea {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-xs);
}

.catalogo-simple__textarea textarea {
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--color-linea);
  border-radius: var(--radio-md);
  font-family: var(--fuente-cuerpo);
  font-size: var(--texto-base);
  resize: vertical;
}
</style>
