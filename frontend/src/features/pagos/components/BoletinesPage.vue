<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";

import { seccionesApi, unidadesApi } from "@/features/catalogo/api/catalogoApi";
import { motivoDelRechazo } from "@/features/notas/api/notasApi";
import { AppButton, CargandoBloque, DataTable, EmptyState, ErrorBanner, FormSelect, PageHeader, TagPill } from "@/shared/components";
import { avisar } from "@/shared/composables/useAvisos";
import { confirmar } from "@/shared/composables/useConfirmar";
import { usePermisos } from "@/shared/permisos";
import type { GradingUnit, ReportCard, Section } from "@/shared/types/models";

import {
  aprobarBoletin,
  aprobarBoletinesEnLote,
  generarBoletines,
  publicarBoletin,
  publicarBoletinesEnLote,
  reportCardsApi,
  type ResultadoPublicacionEnLote,
} from "../api/pagosApi";

// Generar, aprobar y publicar es "editar" en Notas (Dirección);
// Coordinación y Administrador los consultan.
const permisos = usePermisos();
const puedeGestionar = computed(() => permisos.puedeEditar("notas"));

const ETIQUETA_ESTADO: Record<string, string> = {
  borrador: "Borrador",
  aprobado: "Aprobado",
  publicado: "Publicado",
};
const VARIANTE_ESTADO: Record<string, "hoy" | "aviso" | "taller"> = {
  borrador: "hoy",
  aprobado: "aviso",
  publicado: "taller",
};

const cargando = ref(true);
const error = ref("");
const secciones = ref<Section[]>([]);

const seccionElegida = ref("");
const unidades = ref<GradingUnit[]>([]);
const unidadElegida = ref("");
const cargandoUnidades = ref(false);

const boletines = ref<ReportCard[]>([]);
const cargandoBoletines = ref(false);
const enAccionDeLote = ref(false);
const errorAccion = ref("");
const idEnAccion = ref("");
const sinPublicar = ref<ResultadoPublicacionEnLote["no_publicados"]>([]);

const opcionesSeccion = computed(() =>
  secciones.value.map((s) => ({ valor: s.public_id, etiqueta: `${s.grade} ${s.letter ?? ""}`.trimEnd() })),
);
const opcionesUnidad = computed(() =>
  unidades.value.map((u) => ({ valor: u.public_id, etiqueta: `Unidad ${u.number}` })),
);

const borradores = computed(() => boletines.value.filter((b) => b.status === "borrador"));
const aprobados = computed(() => boletines.value.filter((b) => b.status === "aprobado"));
const borradoresIncompletos = computed(() => borradores.value.filter((b) => b.pendientes.length > 0));

/** "Matemática: faltan 2 notas; Física: la unidad suma 60 de 100 puntos" —
 * lo que el boletín mostraría como nota parcial si se aprueba así. El
 * detalle lo arma el servidor. */
function resumenPendientes(boletin: ReportCard): string {
  if (boletin.pendientes.length === 0) return "Completas";
  return boletin.pendientes.map((p) => (p.curso ? `${p.curso}: ${p.detalle}` : p.detalle)).join("; ");
}

const filas = computed(() =>
  boletines.value
    .map((b) => ({ ...b, estudiante: b.student_name, notas: resumenPendientes(b) }))
    .sort((a, b) => a.estudiante.localeCompare(b.estudiante, "es")),
);

async function cargar(): Promise<void> {
  cargando.value = true;
  error.value = "";
  try {
    secciones.value = (await seccionesApi.listar()).results.filter((s) => s.is_active !== false);
    seccionElegida.value = opcionesSeccion.value[0]?.valor ?? "";
  } catch {
    error.value = "No se pudo cargar la lista de secciones. Inténtalo de nuevo.";
  } finally {
    cargando.value = false;
  }
}

async function cargarUnidades(): Promise<void> {
  const seccion = secciones.value.find((s) => s.public_id === seccionElegida.value);
  if (!seccion) {
    unidades.value = [];
    return;
  }
  cargandoUnidades.value = true;
  try {
    unidades.value = (await unidadesApi(seccion.cycle).listar()).results;
    unidadElegida.value = opcionesUnidad.value[0]?.valor ?? "";
  } catch {
    error.value = "No se pudieron cargar las unidades de este ciclo. Inténtalo de nuevo.";
  } finally {
    cargandoUnidades.value = false;
  }
}

async function cargarBoletines(): Promise<void> {
  if (!seccionElegida.value || !unidadElegida.value) {
    boletines.value = [];
    return;
  }
  cargandoBoletines.value = true;
  error.value = "";
  try {
    // Solo la sección y unidad elegidas; el servidor trae nombre y pendientes.
    boletines.value = (
      await reportCardsApi.listar({ section: seccionElegida.value, unit: unidadElegida.value })
    ).results;
  } catch {
    error.value = "No se pudieron cargar los boletines de esta sección. Inténtalo de nuevo.";
  } finally {
    cargandoBoletines.value = false;
  }
}

function seleccion() {
  return { section: seccionElegida.value, unit: unidadElegida.value };
}

async function generar(): Promise<void> {
  enAccionDeLote.value = true;
  errorAccion.value = "";
  try {
    await generarBoletines(seleccion());
    await cargarBoletines();
  } catch (e) {
    errorAccion.value = motivoDelRechazo(e, "No se pudieron generar los boletines. Inténtalo de nuevo.");
  } finally {
    enAccionDeLote.value = false;
  }
}

async function aprobar(boletin: ReportCard): Promise<void> {
  // Aprobar congela el contenido: con notas faltantes, el boletín sale con
  // la nota parcial. Se puede, pero no sin saberlo.
  if (boletin.pendientes.length > 0) {
    const seguir = await confirmar({
      titulo: `¿Aprobar el boletín de ${boletin.student_name}?`,
      mensaje: `Tiene notas pendientes — ${resumenPendientes(boletin)}. Al aprobarlo queda congelado así.`,
      etiquetaConfirmar: "Aprobar igual",
    });
    if (!seguir) return;
  }
  idEnAccion.value = boletin.public_id;
  errorAccion.value = "";
  try {
    await aprobarBoletin(boletin.public_id);
    await cargarBoletines();
  } catch (e) {
    errorAccion.value = motivoDelRechazo(e, "No se pudo aprobar el boletín.");
  } finally {
    idEnAccion.value = "";
  }
}

async function publicar(boletin: ReportCard): Promise<void> {
  idEnAccion.value = boletin.public_id;
  errorAccion.value = "";
  try {
    await publicarBoletin(boletin.public_id);
    await cargarBoletines();
  } catch (e) {
    errorAccion.value = motivoDelRechazo(e, "No se pudo publicar el boletín.");
  } finally {
    idEnAccion.value = "";
  }
}

async function aprobarTodos(): Promise<void> {
  const incompletos = borradoresIncompletos.value.length;
  const seguir = await confirmar({
    titulo: `¿Aprobar ${borradores.value.length} boletines?`,
    mensaje:
      incompletos > 0
        ? `${incompletos} tienen notas pendientes y quedan congelados con la nota parcial. Revisa la columna "Notas" antes de seguir.`
        : "Todos tienen las notas completas. Al aprobarlos quedan congelados.",
    etiquetaConfirmar: "Aprobar todos",
  });
  if (!seguir) return;
  enAccionDeLote.value = true;
  errorAccion.value = "";
  try {
    const { aprobados: cantidad } = await aprobarBoletinesEnLote(seleccion());
    avisar(`${cantidad} boletines aprobados.`);
    await cargarBoletines();
  } catch (e) {
    errorAccion.value = motivoDelRechazo(e, "No se pudieron aprobar los boletines. Inténtalo de nuevo.");
  } finally {
    enAccionDeLote.value = false;
  }
}

async function publicarTodos(): Promise<void> {
  enAccionDeLote.value = true;
  errorAccion.value = "";
  sinPublicar.value = [];
  try {
    const resultado = await publicarBoletinesEnLote(seleccion());
    avisar(`${resultado.publicados} boletines publicados.`);
    sinPublicar.value = resultado.no_publicados;
    await cargarBoletines();
  } catch (e) {
    errorAccion.value = motivoDelRechazo(e, "No se pudieron publicar los boletines. Inténtalo de nuevo.");
  } finally {
    enAccionDeLote.value = false;
  }
}

watch(seccionElegida, cargarUnidades);
watch([seccionElegida, unidadElegida], () => {
  sinPublicar.value = [];
  return cargarBoletines();
});

onMounted(async () => {
  await cargar();
  await cargarUnidades();
});
</script>

<template>
  <section class="boletines-page">
    <PageHeader titulo="Boletines" />

    <ErrorBanner v-if="error" :mensaje="error" etiqueta-accion="Reintentar" @accion="cargar" />
    <CargandoBloque v-else-if="cargando" />

    <template v-else>
      <div class="boletines-page__filtros">
        <FormSelect id="section" etiqueta="Sección" :opciones="opcionesSeccion" v-model="seccionElegida" />
        <FormSelect id="unit" etiqueta="Unidad" :opciones="opcionesUnidad" v-model="unidadElegida" />
      </div>

      <CargandoBloque v-if="cargandoUnidades || cargandoBoletines" />

      <template v-else-if="unidadElegida">
        <div v-if="puedeGestionar" class="boletines-page__barra">
          <AppButton variante="secundario" :deshabilitado="enAccionDeLote" @click="generar">
            Generar boletines
          </AppButton>
          <AppButton
            v-if="borradores.length > 0"
            variante="secundario"
            :deshabilitado="enAccionDeLote"
            @click="aprobarTodos"
          >
            Aprobar los {{ borradores.length }} borradores
          </AppButton>
          <AppButton
            v-if="aprobados.length > 0"
            variante="secundario"
            :deshabilitado="enAccionDeLote"
            @click="publicarTodos"
          >
            Publicar los {{ aprobados.length }} aprobados
          </AppButton>
        </div>

        <ErrorBanner v-if="errorAccion" :mensaje="errorAccion" />

        <div v-if="sinPublicar.length" class="boletines-page__sin-publicar" role="status">
          <p>Quedaron sin publicar:</p>
          <ul>
            <li v-for="item in sinPublicar" :key="item.estudiante">
              <strong>{{ item.estudiante }}</strong> — {{ item.motivo }}
            </li>
          </ul>
        </div>

        <EmptyState
          v-if="boletines.length === 0"
          titulo="No hay boletines"
          :descripcion="puedeGestionar ? 'Genera los boletines de esta sección y unidad para empezar.' : 'Todavía no se generaron los boletines de esta sección y unidad.'"
        />

        <DataTable
          v-else
          class="boletines-page__tabla"
          :columnas="[
            { clave: 'estudiante', etiqueta: 'Estudiante' },
            { clave: 'estado', etiqueta: 'Estado' },
            { clave: 'notas', etiqueta: 'Notas' },
          ]"
          :filas="filas"
        >
          <template #celda-estado="{ fila }">
            <TagPill :variante="VARIANTE_ESTADO[(fila as unknown as ReportCard).status]">
              {{ ETIQUETA_ESTADO[(fila as unknown as ReportCard).status] }}
            </TagPill>
          </template>
          <template #celda-notas="{ fila }">
            <span
              :class="{
                'boletines-page__pendientes':
                  (fila as unknown as ReportCard).status === 'borrador' && (fila as unknown as ReportCard).pendientes.length > 0,
              }"
            >
              {{ (fila as unknown as ReportCard).status === "borrador" ? resumenPendientes(fila as unknown as ReportCard) : "Congeladas al aprobar" }}
            </span>
          </template>
          <template v-if="puedeGestionar" #acciones="{ fila }">
            <button
              v-if="(fila as unknown as ReportCard).status === 'borrador'"
              type="button"
              class="boletines-page__accion"
              :disabled="enAccionDeLote || idEnAccion === (fila as unknown as ReportCard).public_id"
              @click="aprobar(fila as unknown as ReportCard)"
            >
              Aprobar
            </button>
            <button
              v-else-if="(fila as unknown as ReportCard).status === 'aprobado'"
              type="button"
              class="boletines-page__accion"
              :disabled="enAccionDeLote || idEnAccion === (fila as unknown as ReportCard).public_id"
              @click="publicar(fila as unknown as ReportCard)"
            >
              Publicar
            </button>
          </template>
        </DataTable>
      </template>
    </template>
  </section>
</template>

<style scoped>

.boletines-page__filtros {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 13rem), 1fr));
  gap: var(--espacio-md) var(--espacio-lg);
  align-items: end;
  max-width: 52rem;
}

.boletines-page__barra {
  display: flex;
  flex-wrap: wrap;
  gap: var(--espacio-md);
  margin-top: var(--espacio-lg);
}

.boletines-page__sin-publicar {
  margin-top: var(--espacio-lg);
  padding: var(--espacio-md) var(--espacio-lg);
  border: 1px solid var(--color-linea);
  border-radius: var(--radio-md);
}

.boletines-page__sin-publicar p {
  margin: 0 0 var(--espacio-xs);
  font-weight: 600;
}

.boletines-page__sin-publicar ul {
  margin: 0;
  padding-left: 1.2rem;
}

.boletines-page__pendientes {
  color: var(--color-peligro);
}

.boletines-page__tabla {
  margin-top: var(--espacio-lg);
}

.boletines-page__accion {
  background: none;
  border: none;
  color: var(--color-accion);
  font-size: var(--texto-sm);
  font-weight: 600;
  cursor: pointer;
  padding: 0.3rem 0.5rem;
}
</style>
