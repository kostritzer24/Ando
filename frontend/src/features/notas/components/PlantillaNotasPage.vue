<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";

import { assignmentsApi } from "@/features/asignaciones/api/asignacionesApi";
import { AppButton, AppPanel, CampoArchivo, CargandoBloque, ErrorBanner, FormSelect, PageHeader } from "@/shared/components";
import type { TeacherAssignment } from "@/shared/types/models";

import {
  descargarPlantillaNotas,
  previsualizarPlantillaNotas,
  subirPlantillaNotas,
  unidadesDeCiclo,
} from "../api/notasApi";
import type { ResultadoSubidaNotas, ResumenVistaPrevia } from "../api/notasApi";

const cargando = ref(true);
const error = ref("");
const asignaciones = ref<TeacherAssignment[]>([]);
const unidadesDisponibles = ref<{ valor: string; etiqueta: string }[]>([]);

const asignacionElegida = ref("");
const unidadElegida = ref("");
const archivoElegido = ref<File | null>(null);

const previsualizando = ref(false);
const vistaPrevia = ref<ResumenVistaPrevia | null>(null);
const confirmando = ref(false);
const resultado = ref<ResultadoSubidaNotas | null>(null);

const opcionesAsignacion = computed(() =>
  asignaciones.value.map((a) => ({
    valor: a.public_id,
    etiqueta: `${a.course_name} — ${a.section_grade} ${a.section_letter}`.trim(),
  })),
);

async function cargar(): Promise<void> {
  cargando.value = true;
  error.value = "";
  try {
    asignaciones.value = (await assignmentsApi.listar()).results;
    asignacionElegida.value = opcionesAsignacion.value[0]?.valor ?? "";
  } catch {
    error.value = "No se pudo cargar la lista de asignaciones. Inténtalo de nuevo.";
  } finally {
    cargando.value = false;
  }
}

async function cargarUnidades(): Promise<void> {
  const asignacion = asignaciones.value.find((a) => a.public_id === asignacionElegida.value);
  if (!asignacion) {
    unidadesDisponibles.value = [];
    return;
  }
  const unidades = (await unidadesDeCiclo(asignacion.cycle).listar()).results;
  unidadesDisponibles.value = unidades.map((u) => ({ valor: u.public_id, etiqueta: `Unidad ${u.number}` }));
  unidadElegida.value = unidadesDisponibles.value[0]?.valor ?? "";
}

async function descargar(): Promise<void> {
  if (!asignacionElegida.value || !unidadElegida.value) return;
  error.value = "";
  try {
    const { blob, nombreArchivo } = await descargarPlantillaNotas(asignacionElegida.value, unidadElegida.value);
    const url = URL.createObjectURL(blob);
    const enlace = document.createElement("a");
    enlace.href = url;
    enlace.download = nombreArchivo;
    enlace.click();
    URL.revokeObjectURL(url);
  } catch {
    error.value = "No se pudo generar la plantilla. Inténtalo de nuevo.";
  }
}

function alElegirArchivo(archivo: File | null): void {
  archivoElegido.value = archivo;
  vistaPrevia.value = null;
  resultado.value = null;
}

async function previsualizar(): Promise<void> {
  if (!archivoElegido.value) return;
  previsualizando.value = true;
  error.value = "";
  resultado.value = null;
  try {
    vistaPrevia.value = await previsualizarPlantillaNotas({
      assignment: asignacionElegida.value,
      unit: unidadElegida.value,
      file: archivoElegido.value,
    });
  } catch {
    error.value = "No se pudo leer el archivo. Inténtalo de nuevo.";
  } finally {
    previsualizando.value = false;
  }
}

async function confirmar(): Promise<void> {
  if (!archivoElegido.value) return;
  confirmando.value = true;
  error.value = "";
  try {
    resultado.value = await subirPlantillaNotas({
      assignment: asignacionElegida.value,
      unit: unidadElegida.value,
      file: archivoElegido.value,
    });
    vistaPrevia.value = null;
  } catch {
    error.value = "No se pudo guardar la plantilla. Inténtalo de nuevo.";
  } finally {
    confirmando.value = false;
  }
}

watch(asignacionElegida, cargarUnidades);

onMounted(async () => {
  await cargar();
  await cargarUnidades();
});
</script>

<template>
  <section class="plantilla-notas">
    <PageHeader titulo="Plantilla de calificaciones" />

    <ErrorBanner v-if="error" :mensaje="error" etiqueta-accion="Reintentar" @accion="cargar" />
    <CargandoBloque v-else-if="cargando" />

    <template v-else>
      <div class="plantilla-notas__pasos">
        <AppPanel titulo="1. Descarga la plantilla" descripcion="Trae la lista de la sección con las actividades de la unidad.">
          <div class="plantilla-notas__campos">
            <div class="plantilla-notas__filtros">
              <FormSelect
                id="assignment"
                etiqueta="Curso y sección"
                :opciones="opcionesAsignacion"
                v-model="asignacionElegida"
              />
              <FormSelect id="unit" etiqueta="Unidad" :opciones="unidadesDisponibles" v-model="unidadElegida" />
            </div>
            <AppButton variante="secundario" :deshabilitado="!unidadElegida" @click="descargar">
              Descargar plantilla
            </AppButton>
          </div>
        </AppPanel>

        <AppPanel titulo="2. Sube la plantilla llena" descripcion="Primero la revisas; nada se guarda hasta que confirmes.">
          <div class="plantilla-notas__campos">
            <CampoArchivo id="file" etiqueta="Archivo de Excel (.xlsx)" accept=".xlsx" @elegir="alElegirArchivo" />
            <AppButton :deshabilitado="!archivoElegido || previsualizando" @click="previsualizar">
              {{ previsualizando ? "Revisando…" : "Ver antes de guardar" }}
            </AppButton>
          </div>
        </AppPanel>
      </div>

      <div v-if="vistaPrevia && !vistaPrevia.errores" class="plantilla-notas__vista-previa">
        <p class="plantilla-notas__vista-titulo">{{ vistaPrevia.filas }} filas leídas, sin errores:</p>
        <ul>
          <li>{{ vistaPrevia.resumen.crear }} notas nuevas</li>
          <li v-if="vistaPrevia.resumen.correccion">
            {{ vistaPrevia.resumen.correccion }} se corrigen directo (todavía no pasó la fecha de entrega)
          </li>
          <li>{{ vistaPrevia.resumen.modificacion }} van a generar una solicitud de corrección</li>
          <li>{{ vistaPrevia.resumen.sin_cambio }} sin cambios</li>
        </ul>
        <AppButton :deshabilitado="confirmando" @click="confirmar">
          {{ confirmando ? "Guardando…" : "Confirmar y guardar" }}
        </AppButton>
      </div>

      <div v-if="vistaPrevia?.errores?.length" class="plantilla-notas__errores" role="alert">
        <p>La plantilla tiene errores y no se guardó ningún registro. Corrige estas filas y vuelve a subirla:</p>
        <ul>
          <li v-for="(err, indice) in vistaPrevia.errores" :key="indice">{{ err }}</li>
        </ul>
      </div>

      <p v-if="resultado?.creados !== undefined" class="plantilla-notas__exito">
        Se guardaron {{ resultado.creados }} notas
        <template v-if="resultado.correcciones">, se corrigieron {{ resultado.correcciones }}</template>
        <template v-if="resultado.solicitudes_de_modificacion">
          y se generaron {{ resultado.solicitudes_de_modificacion }} solicitudes de corrección.
        </template>
      </p>
      <div v-if="resultado?.errores?.length" class="plantilla-notas__errores">
        <p>No se guardó nada — la plantilla tiene errores:</p>
        <ul>
          <li v-for="(err, indice) in resultado.errores" :key="indice">{{ err }}</li>
        </ul>
      </div>
    </template>
  </section>
</template>

<style scoped>
.plantilla-notas__pasos {
  display: grid;
  gap: var(--espacio-lg);
  align-items: start;
}

.plantilla-notas__campos {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--espacio-lg);
}

.plantilla-notas__campos > :not(button) {
  align-self: stretch;
}

.plantilla-notas__filtros {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 12rem), 1fr));
  gap: var(--espacio-md);
}

.plantilla-notas__vista-previa {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--espacio-md);
  padding: var(--espacio-lg);
  background: var(--color-accion-suave);
  border-left: 4px solid var(--color-accion);
  border-radius: var(--radio-md);
}

.plantilla-notas__vista-previa p,
.plantilla-notas__vista-previa ul {
  margin: 0;
}

.plantilla-notas__vista-previa ul {
  padding-left: var(--espacio-xl);
}

.plantilla-notas__vista-titulo {
  font-weight: 600;
}

.plantilla-notas__exito {
  color: var(--color-exito);
  font-weight: 600;
}

.plantilla-notas__errores {
  padding: var(--espacio-lg);
  background: var(--color-etiqueta-alerta-fondo);
  color: var(--color-etiqueta-alerta-texto);
  border-left: 4px solid var(--color-peligro);
  border-radius: var(--radio-md);
}

.plantilla-notas__errores p {
  margin: 0 0 var(--espacio-sm);
  font-weight: 600;
}

.plantilla-notas__errores ul {
  margin: 0;
  padding-left: var(--espacio-xl);
}

@media (min-width: 64rem) {
  .plantilla-notas__pasos {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
