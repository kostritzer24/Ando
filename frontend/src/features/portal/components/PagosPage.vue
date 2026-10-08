<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";

import {
  consultarSolvencia,
  descargarArchivo,
  descargarDocumento,
  issuedDocumentsApi,
} from "@/features/pagos/api/pagosApi";
import type { EstadoSolvencia } from "@/features/pagos/api/pagosApi";
import { usePortalStore } from "@/features/portal/stores/portalStore";
import { CargandoBloque, ErrorBanner, PageHeader } from "@/shared/components";
import type { IssuedDocument } from "@/shared/types/models";

const MESES = [
  "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
];
function nombreMes(numero: number): string {
  return MESES[numero - 1] ?? String(numero);
}

const portal = usePortalStore();

const cargando = ref(true);
const error = ref("");
const solvencia = ref<EstadoSolvencia | null>(null);
const constancias = ref<IssuedDocument[]>([]);
const descargandoId = ref("");
const errorDescarga = ref("");

const inscripcionAcademica = computed(
  () => portal.inscripcionesDelSeleccionado.find((i) => i.section_type === "academica"),
);

async function cargar(): Promise<void> {
  const inscripcion = inscripcionAcademica.value;
  if (!inscripcion) return;
  cargando.value = true;
  error.value = "";
  try {
    const [solvenciaResp, documentosResp] = await Promise.all([
      consultarSolvencia(inscripcion.public_id),
      issuedDocumentsApi.listar(),
    ]);
    solvencia.value = solvenciaResp;
    constancias.value = documentosResp.results.filter(
      (d) => d.document_type === "Constancia de solvencia" && d.enrollment === inscripcion.public_id,
    );
  } catch {
    error.value = "No se pudo cargar el estado de pagos. Inténtalo de nuevo.";
  } finally {
    cargando.value = false;
  }
}

async function descargar(documento: IssuedDocument): Promise<void> {
  descargandoId.value = documento.public_id;
  errorDescarga.value = "";
  try {
    const { blob, nombreArchivo } = await descargarDocumento(documento.public_id);
    descargarArchivo(blob, nombreArchivo);
  } catch {
    errorDescarga.value = "No se pudo descargar la constancia. Inténtalo de nuevo.";
  } finally {
    descargandoId.value = "";
  }
}

watch(() => portal.estudianteSeleccionadoId, cargar);
onMounted(cargar);
</script>

<template>
  <section class="pagos-page">
    <PageHeader titulo="Pagos y solvencia" />

    <ErrorBanner v-if="error" :mensaje="error" etiqueta-accion="Reintentar" @accion="cargar" />
    <CargandoBloque v-else-if="cargando" />

    <template v-else-if="solvencia">
      <div
        class="pagos-page__estado"
        :class="{
          'pagos-page__estado--al-dia': solvencia.solvente,
          'pagos-page__estado--pendiente': !solvencia.solvente,
        }"
      >
        <p v-if="solvencia.tiene_beca"><strong>Solvente por beca.</strong></p>
        <p v-else-if="solvencia.solvente"><strong>Al día con los pagos.</strong></p>
        <p v-else><strong>Hay meses pendientes de pago.</strong></p>
        <p v-if="!solvencia.tiene_beca && solvencia.meses_pendientes.length > 0">
          Meses pendientes:
          {{ solvencia.meses_pendientes.map(([anio, mes]) => `${nombreMes(mes)} ${anio}`).join(", ") }}
        </p>
      </div>

      <h2>Constancias de solvencia</h2>
      <ErrorBanner v-if="errorDescarga" :mensaje="errorDescarga" />
      <p v-if="constancias.length === 0" class="pagos-page__vacio">
        Todavía no se emitió ninguna constancia de solvencia. Pedila en la oficina de pagos.
      </p>
      <ul v-else class="pagos-page__lista">
        <li v-for="documento in constancias" :key="documento.public_id" class="pagos-page__fila">
          <span>{{ new Date(documento.issued_at).toLocaleDateString("es-GT") }}</span>
          <button
            type="button"
            class="pagos-page__accion"
            :disabled="descargandoId === documento.public_id"
            @click="descargar(documento)"
          >
            Descargar
          </button>
        </li>
      </ul>
    </template>
  </section>
</template>

<style scoped>

.pagos-page h2 {
  font-family: var(--fuente-titulo);
  font-size: var(--texto-base);
  margin: var(--espacio-xl) 0 var(--espacio-md);
}

.pagos-page__estado {
  padding: var(--espacio-lg);
  border-radius: var(--radio-md);
  display: flex;
  flex-direction: column;
  gap: var(--espacio-sm);
}

.pagos-page__estado--al-dia {
  background: var(--color-etiqueta-taller-fondo);
  color: var(--color-etiqueta-taller-texto);
}

.pagos-page__estado--pendiente {
  background: var(--color-etiqueta-alerta-fondo);
  color: var(--color-etiqueta-alerta-texto);
}

.pagos-page__vacio {
  color: var(--color-tinta-suave);
}

.pagos-page__lista {
  list-style: none;
  margin: 0;
  padding: 0;
}

.pagos-page__fila {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--espacio-sm) 0;
  border-bottom: 1px solid var(--color-linea);
}

.pagos-page__accion {
  background: none;
  border: none;
  color: var(--color-accion);
  font-size: var(--texto-sm);
  font-weight: 600;
  cursor: pointer;
  padding: 0.3rem 0.5rem;
}
</style>
