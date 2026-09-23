<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";

import { enrollmentsApi, studentsApi } from "@/features/estudiantes/api/estudiantesApi";
import { AppButton, DataTable, ErrorBanner, FormField, FormSelect } from "@/shared/components";
import type { Enrollment, Payment, Student } from "@/shared/types/models";

import {
  consultarSolvencia,
  descargarArchivo,
  emitirConstanciaSolvencia,
  paymentsApi,
} from "../api/pagosApi";
import type { EstadoSolvencia } from "../api/pagosApi";

const MESES = [
  "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
];

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

const anioActual = new Date().getFullYear();
const formulario = reactive({
  period_month: "1",
  period_year: String(anioActual),
  amount: "",
  payment_date: "",
  receipt_number: "",
});

const opcionesInscripcion = computed(() =>
  inscripciones.value.map((i) => {
    const estudiante = estudiantes.value.find((e) => e.public_id === i.student);
    const nombre = estudiante ? `${estudiante.first_name} ${estudiante.last_name}` : "—";
    const codigo = estudiante ? ` (${estudiante.internal_code})` : "";
    return { valor: i.public_id, etiqueta: `${nombre}${codigo}` };
  }),
);

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
    error.value = "No se pudo cargar la lista de estudiantes. Probá de nuevo.";
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
    error.value = "No se pudo cargar la solvencia de este estudiante. Probá de nuevo.";
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
    errorPago.value = "No se pudo registrar el pago. Revisá los datos (el recibo debe ser único) e intentá de nuevo.";
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
    errorEmision.value = "No se pudo emitir la constancia. Probá de nuevo.";
  } finally {
    emitiendo.value = false;
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
    <h1>Pagos y solvencia</h1>

    <ErrorBanner v-if="error" :mensaje="error" etiqueta-accion="Reintentar" @accion="cargar" />
    <p v-else-if="cargando">Cargando…</p>

    <template v-else>
      <FormSelect
        id="inscripcion"
        etiqueta="Estudiante"
        :opciones="opcionesInscripcion"
        v-model="inscripcionElegida"
      />

      <p v-if="cargandoDetalle">Cargando…</p>

      <template v-else-if="inscripcionElegida && solvencia">
        <div
          class="pagos-page__solvencia"
          :class="{ 'pagos-page__solvencia--al-dia': solvencia.solvente, 'pagos-page__solvencia--pendiente': !solvencia.solvente }"
        >
          <p v-if="solvencia.tiene_beca"><strong>Solvente por beca.</strong></p>
          <p v-else-if="solvencia.solvente"><strong>Al día con sus pagos.</strong></p>
          <p v-else><strong>No está solvente.</strong></p>
          <p v-if="!solvencia.tiene_beca && solvencia.meses_pendientes.length > 0">
            Meses pendientes:
            {{ solvencia.meses_pendientes.map(([anio, mes]) => `${nombreMes(mes)} ${anio}`).join(", ") }}
          </p>

          <ErrorBanner v-if="errorEmision" :mensaje="errorEmision" />
          <AppButton
            variante="secundario"
            :deshabilitado="!solvencia.solvente || emitiendo"
            @click="emitirConstancia"
          >
            {{ emitiendo ? "Generando…" : "Emitir constancia de solvencia" }}
          </AppButton>
        </div>

        <h2>Registrar pago</h2>
        <ErrorBanner v-if="errorPago" :mensaje="errorPago" />
        <form class="pagos-page__formulario" @submit.prevent="registrarPago">
          <FormSelect id="period_month" etiqueta="Mes" :opciones="opcionesMes" v-model="formulario.period_month" />
          <FormField id="period_year" etiqueta="Año" tipo="number" v-model="formulario.period_year" />
          <FormField id="amount" etiqueta="Monto (Q)" tipo="number" step="0.01" v-model="formulario.amount" />
          <FormField id="payment_date" etiqueta="Fecha de pago" tipo="date" v-model="formulario.payment_date" />
          <FormField id="receipt_number" etiqueta="Número de recibo" v-model="formulario.receipt_number" />
          <AppButton tipo="submit" :deshabilitado="guardando">
            {{ guardando ? "Guardando…" : "Registrar pago" }}
          </AppButton>
        </form>

        <h2>Pagos registrados</h2>
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
        />
      </template>
    </template>
  </section>
</template>

<style scoped>
.pagos-page h1 {
  font-family: var(--fuente-titulo);
  font-size: var(--texto-md);
  margin: 0 0 var(--espacio-xl);
}

.pagos-page h2 {
  font-family: var(--fuente-titulo);
  font-size: var(--texto-base);
  margin: var(--espacio-xl) 0 var(--espacio-md);
}

.pagos-page__solvencia {
  margin-top: var(--espacio-lg);
  padding: var(--espacio-lg);
  border-radius: var(--radio-md);
  display: flex;
  flex-direction: column;
  gap: var(--espacio-sm);
  align-items: flex-start;
}

.pagos-page__solvencia--al-dia {
  background: var(--color-etiqueta-taller-fondo);
  color: var(--color-etiqueta-taller-texto);
}

.pagos-page__solvencia--pendiente {
  background: var(--color-etiqueta-alerta-fondo);
  color: var(--color-etiqueta-alerta-texto);
}

.pagos-page__formulario {
  display: flex;
  flex-wrap: wrap;
  gap: var(--espacio-lg);
  align-items: flex-end;
}

.pagos-page__vacio {
  color: var(--color-tinta-suave);
}
</style>
