<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";

import { enrollmentsApi, studentsApi } from "@/features/estudiantes/api/estudiantesApi";
import { AppButton, CargandoBloque, DataTable, ErrorBanner, FormField, FormSelect, PageHeader } from "@/shared/components";
import { usePermisos } from "@/shared/permisos";
import type { Enrollment, Payment, Student } from "@/shared/types/models";

import {
  consultarSolvencia,
  descargarArchivo,
  emitirConstanciaSolvencia,
  paymentsApi,
} from "../api/pagosApi";
import type { EstadoSolvencia } from "../api/pagosApi";
import { descargarReportePdf } from "@/features/reportes/api/reportesApi";

const MESES = [
  "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
];

// Registrar pagos y emitir constancias es "editar" en Pagos (Dirección y
// Encargado de pagos); Coordinación y Administrador consultan.
const permisos = usePermisos();
const puedeRegistrar = computed(() => permisos.puedeEditar("pagos_solvencia"));

const cargando = ref(true);
const error = ref("");
const inscripciones = ref<Enrollment[]>([]);
const estudiantes = ref<Student[]>([]);

const inscripcionElegida = ref("");
const cargandoDetalle = ref(false);
const solvencia = ref<EstadoSolvencia | null>(null);
const pagos = ref<Payment[]>([]);

const guardando = ref(false);
const errorPago = ref("");
const emitiendo = ref(false);
const errorEmision = ref("");
const descargandoReporte = ref(false);

const anioActual = new Date().getFullYear();
const formulario = reactive({
  period_month: "1",
  period_year: String(anioActual),
  amount: "",
  payment_date: "",
  receipt_number: "",
});

// Con decenas de estudiantes, elegir de una lista plana es lento: se puede
// acotar por sección y buscar por nombre o código.
const filtroSeccion = ref("");
const busqueda = ref("");

function etiquetaSeccion(i: Enrollment): string {
  return `${i.section_grade ?? ""} ${i.section_letter ?? ""}`.trim();
}

const opcionesSeccion = computed(() => {
  const nombres = [...new Set(inscripciones.value.map(etiquetaSeccion))].filter(Boolean).sort();
  return [{ valor: "", etiqueta: "Todas las secciones" }, ...nombres.map((n) => ({ valor: n, etiqueta: n }))];
});

function sinTildes(texto: string): string {
  return texto.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
}

const opcionesInscripcion = computed(() => {
  const termino = sinTildes(busqueda.value.trim());
  return inscripciones.value
    .filter((i) => !filtroSeccion.value || etiquetaSeccion(i) === filtroSeccion.value)
    .map((i) => {
      const estudiante = estudiantes.value.find((e) => e.public_id === i.student);
      const nombre = estudiante ? `${estudiante.first_name} ${estudiante.last_name}` : "—";
      const codigo = estudiante ? ` (${estudiante.internal_code})` : "";
      return { valor: i.public_id, etiqueta: `${nombre}${codigo}` };
    })
    .filter((o) => !termino || sinTildes(o.etiqueta).includes(termino));
});

// Si el filtro deja fuera al estudiante elegido, pasa al primero que sí cumpla.
watch(opcionesInscripcion, (opciones) => {
  if (!opciones.some((o) => o.valor === inscripcionElegida.value)) {
    inscripcionElegida.value = opciones[0]?.valor ?? "";
  }
});

const opcionesMes = MESES.map((nombre, indice) => ({ valor: String(indice + 1), etiqueta: nombre }));

function nombreMes(numero: number): string {
  return MESES[numero - 1] ?? String(numero);
}

async function cargar(): Promise<void> {
  cargando.value = true;
  error.value = "";
  try {
    const [inscripcionesResp, estudiantesResp] = await Promise.all([
      enrollmentsApi.listar(),
      studentsApi.listar(),
    ]);
    inscripciones.value = inscripcionesResp.results.filter((i) => i.status === "activo");
    estudiantes.value = estudiantesResp.results;
    inscripcionElegida.value = opcionesInscripcion.value[0]?.valor ?? "";
  } catch {
    error.value = "No se pudo cargar la lista de estudiantes. Inténtalo de nuevo.";
  } finally {
    cargando.value = false;
  }
}

async function cargarDetalle(): Promise<void> {
  if (!inscripcionElegida.value) {
    solvencia.value = null;
    pagos.value = [];
    return;
  }
  cargandoDetalle.value = true;
  error.value = "";
  try {
    const [solvenciaResp, pagosResp] = await Promise.all([
      consultarSolvencia(inscripcionElegida.value),
      paymentsApi.listar(),
    ]);
    solvencia.value = solvenciaResp;
    pagos.value = pagosResp.results.filter((p) => p.enrollment === inscripcionElegida.value);
  } catch {
    error.value = "No se pudo cargar la solvencia de este estudiante. Inténtalo de nuevo.";
  } finally {
    cargandoDetalle.value = false;
  }
}

async function registrarPago(): Promise<void> {
  guardando.value = true;
  errorPago.value = "";
  try {
    await paymentsApi.crear({
      enrollment: inscripcionElegida.value,
      period_month: Number(formulario.period_month),
      period_year: Number(formulario.period_year),
      amount: formulario.amount,
      payment_date: formulario.payment_date,
      receipt_number: formulario.receipt_number,
    } as Partial<Payment>);
    formulario.amount = "";
    formulario.payment_date = "";
    formulario.receipt_number = "";
    await cargarDetalle();
  } catch {
    errorPago.value = "No se pudo registrar el pago. Revisa los datos (el recibo debe ser único) e inténtalo de nuevo.";
  } finally {
    guardando.value = false;
  }
}

async function emitirConstancia(): Promise<void> {
  emitiendo.value = true;
  errorEmision.value = "";
  try {
    const { blob, nombreArchivo } = await emitirConstanciaSolvencia(inscripcionElegida.value);
    descargarArchivo(blob, nombreArchivo);
  } catch {
    errorEmision.value = "No se pudo emitir la constancia. Inténtalo de nuevo.";
  } finally {
    emitiendo.value = false;
  }
}

async function descargarReporteInsolventes(): Promise<void> {
  descargandoReporte.value = true;
  error.value = "";
  try {
    const { blob, nombreArchivo } = await descargarReportePdf("insolvent-students", {});
    descargarArchivo(blob, nombreArchivo);
  } catch {
    error.value = "No se pudo generar el reporte. Inténtalo de nuevo.";
  } finally {
    descargandoReporte.value = false;
  }
}

watch(inscripcionElegida, cargarDetalle);

onMounted(async () => {
  await cargar();
  await cargarDetalle();
});
</script>

<template>
  <section class="pagos-page">
    <PageHeader titulo="Pagos y solvencia" descripcion="Estado de pagos de cada estudiante y constancias de solvencia.">
      <template #acciones>
        <AppButton variante="secundario" :deshabilitado="cargando || descargandoReporte" @click="descargarReporteInsolventes">
          {{ descargandoReporte ? "Generando…" : "Reporte de estudiantes insolventes" }}
        </AppButton>
      </template>
    </PageHeader>

    <ErrorBanner v-if="error" :mensaje="error" etiqueta-accion="Reintentar" @accion="cargar" />
    <CargandoBloque v-else-if="cargando" />

    <template v-else>
      <div class="pagos-page__selector">
        <FormSelect id="filtro-seccion" etiqueta="Sección" :opciones="opcionesSeccion" v-model="filtroSeccion" />
        <FormField id="busqueda-estudiante" etiqueta="Buscar estudiante" v-model="busqueda" />
        <FormSelect
          id="inscripcion"
          etiqueta="Estudiante"
          :opciones="opcionesInscripcion"
          v-model="inscripcionElegida"
        />
      </div>

      <CargandoBloque v-if="cargandoDetalle" :filas="3" />

      <template v-else-if="inscripcionElegida && solvencia">
        <div
          class="pagos-page__solvencia"
          :class="solvencia.solvente ? 'pagos-page__solvencia--al-dia' : 'pagos-page__solvencia--pendiente'"
        >
          <div class="pagos-page__solvencia-texto">
            <p v-if="solvencia.tiene_beca" class="pagos-page__solvencia-titulo">Solvente por beca.</p>
            <p v-else-if="solvencia.solvente" class="pagos-page__solvencia-titulo">Al día con sus pagos.</p>
            <p v-else class="pagos-page__solvencia-titulo">No está solvente.</p>
            <p v-if="!solvencia.tiene_beca && solvencia.meses_pendientes.length > 0">
              Meses pendientes:
              {{ solvencia.meses_pendientes.map(([anio, mes]) => `${nombreMes(mes)} ${anio}`).join(", ") }}
            </p>
          </div>
          <AppButton
            v-if="puedeRegistrar"
            variante="secundario"
            :deshabilitado="!solvencia.solvente || emitiendo"
            @click="emitirConstancia"
          >
            {{ emitiendo ? "Generando…" : "Emitir constancia de solvencia" }}
          </AppButton>
          <ErrorBanner v-if="errorEmision" :mensaje="errorEmision" class="pagos-page__error-emision" />
        </div>

        <div class="pagos-page__paneles" :class="{ 'pagos-page__paneles--uno': !puedeRegistrar }">
          <section v-if="puedeRegistrar" class="pagos-page__panel" aria-labelledby="titulo-registrar">
            <h2 id="titulo-registrar">Registrar pago</h2>
            <form class="pagos-page__formulario" @submit.prevent="registrarPago">
              <ErrorBanner v-if="errorPago" :mensaje="errorPago" />
              <div class="pagos-page__dos-columnas">
                <FormSelect id="period_month" etiqueta="Mes" :opciones="opcionesMes" v-model="formulario.period_month" />
                <FormField id="period_year" etiqueta="Año" tipo="number" v-model="formulario.period_year" />
              </div>
              <div class="pagos-page__dos-columnas">
                <FormField id="amount" etiqueta="Monto (Q)" tipo="number" step="0.01" inputmode="decimal" v-model="formulario.amount" />
                <FormField id="payment_date" etiqueta="Fecha de pago" tipo="date" v-model="formulario.payment_date" />
              </div>
              <FormField id="receipt_number" etiqueta="Número de recibo" v-model="formulario.receipt_number" />
              <AppButton tipo="submit" bloque :deshabilitado="guardando">
                {{ guardando ? "Guardando…" : "Registrar pago" }}
              </AppButton>
            </form>
          </section>

          <section class="pagos-page__panel pagos-page__panel--lista" aria-labelledby="titulo-registrados">
            <h2 id="titulo-registrados">Pagos registrados</h2>
            <p v-if="pagos.length === 0" class="pagos-page__vacio">Todavía no hay pagos registrados.</p>
            <DataTable
              v-else
              :columnas="[
                { clave: 'mes', etiqueta: 'Mes' },
                { clave: 'period_year', etiqueta: 'Año' },
                { clave: 'amount', etiqueta: 'Monto' },
                { clave: 'payment_date', etiqueta: 'Fecha de pago' },
                { clave: 'receipt_number', etiqueta: 'Recibo' },
              ]"
              :filas="pagos.map((p) => ({ ...p, mes: nombreMes(p.period_month) }))"
              :por-pagina="12"
            />
          </section>
        </div>
      </template>
    </template>
  </section>
</template>

<style scoped>
.pagos-page__selector {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-md);
  max-width: 28rem;
}

.pagos-page__solvencia {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--espacio-md);
  padding: var(--espacio-lg);
  border-radius: var(--radio-lg);
  border-left: 4px solid currentColor;
}

.pagos-page__solvencia p {
  margin: 0;
}

.pagos-page__solvencia-titulo {
  font-family: var(--fuente-titulo);
  font-size: var(--texto-md);
  font-weight: 700;
}

.pagos-page__solvencia-texto {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-2xs);
}

.pagos-page__solvencia--al-dia {
  background: var(--color-etiqueta-taller-fondo);
  color: var(--color-etiqueta-taller-texto);
}

.pagos-page__solvencia--pendiente {
  background: var(--color-etiqueta-alerta-fondo);
  color: var(--color-etiqueta-alerta-texto);
}

.pagos-page__error-emision {
  margin: 0;
  width: 100%;
}

.pagos-page__paneles {
  display: grid;
  gap: var(--espacio-xl);
  align-items: start;
}

.pagos-page__panel {
  min-width: 0;
}

.pagos-page__panel h2 {
  font-size: var(--texto-md);
  margin-bottom: var(--espacio-md);
}

.pagos-page__panel:not(.pagos-page__panel--lista) {
  padding: var(--espacio-lg);
  background: var(--color-papel);
  border: 1px solid var(--color-linea);
  border-radius: var(--radio-lg);
}

.pagos-page__formulario {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-lg);
}

.pagos-page__dos-columnas {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: var(--espacio-md);
}

.pagos-page__vacio {
  margin: 0;
  color: var(--color-tinta-suave);
}

@media (min-width: 40rem) {
  .pagos-page__solvencia {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    padding: var(--espacio-lg) var(--espacio-xl);
  }
}

@media (min-width: 64rem) {
  .pagos-page__paneles {
    grid-template-columns: 22rem minmax(0, 1fr);
  }

  .pagos-page__paneles--uno {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
