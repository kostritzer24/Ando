<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { assignmentsApi } from "@/features/asignaciones/api/asignacionesApi";
import { seccionesApi } from "@/features/catalogo/api/catalogoApi";
import { useAuthStore } from "@/features/auth/stores/authStore";
import { AppButton, AppPanel, CampoArchivo, CargandoBloque, ErrorBanner, FormField, FormSelect, PageHeader } from "@/shared/components";
import type { Section, TeacherAssignment } from "@/shared/types/models";

import { descargarPlantillaAsistencia, subirPlantillaAsistencia } from "../api/asistenciaApi";
import type { ResultadoPlantilla } from "../api/asistenciaApi";

const auth = useAuthStore();
// docs/permisos-roles.md: la plantilla de talleres es DIR/TALL — el
// resto de roles docentes de la jornada matutina no la necesita (RF-21
// es específico para las secciones de taller).
const puedeUsarPlantilla = computed(() =>
  ["Dirección", "Tallerista"].includes(auth.usuario?.role_name ?? ""),
);

const cargando = ref(true);
const error = ref("");
const secciones = ref<Section[]>([]);
const asignaciones = ref<TeacherAssignment[]>([]);

const seccionElegida = ref("");
const fecha = ref(new Date().toISOString().slice(0, 10));
const archivoElegido = ref<File | null>(null);
const subiendo = ref(false);
const resultado = ref<ResultadoPlantilla | null>(null);

// `/sections/` vive detrás del área "datos_maestros" — Tallerista no
// llega ahí (docs/permisos-roles.md), así que su lista de talleres sale
// de sus propias asignaciones, no del catálogo completo.
const opcionesSeccion = computed(() => {
  if (auth.usuario?.role_name === "Dirección") {
    return secciones.value
      .filter((s) => s.type === "taller")
      .map((s) => ({ valor: s.public_id, etiqueta: `${s.grade} ${s.letter}`.trim() }));
  }
  const vistas = new Set<string>();
  const opciones: { valor: string; etiqueta: string }[] = [];
  for (const asignacion of asignaciones.value) {
    if (asignacion.section_type !== "taller" || vistas.has(asignacion.section)) continue;
    vistas.add(asignacion.section);
    opciones.push({
      valor: asignacion.section,
      etiqueta: `${asignacion.section_grade} ${asignacion.section_letter}`.trim(),
    });
  }
  return opciones;
});

async function cargar(): Promise<void> {
  cargando.value = true;
  error.value = "";
  try {
    asignaciones.value = (await assignmentsApi.listar()).results;
    if (auth.usuario?.role_name === "Dirección") {
      secciones.value = (await seccionesApi.listar()).results;
    }
    seccionElegida.value = opcionesSeccion.value[0]?.valor ?? "";
  } catch {
    error.value = "No se pudo cargar la lista de talleres. Probá de nuevo.";
  } finally {
    cargando.value = false;
  }
}

async function descargar(): Promise<void> {
  if (!seccionElegida.value) return;
  error.value = "";
  try {
    const { blob, nombreArchivo } = await descargarPlantillaAsistencia(seccionElegida.value, fecha.value);
    const url = URL.createObjectURL(blob);
    const enlace = document.createElement("a");
    enlace.href = url;
    enlace.download = nombreArchivo;
    enlace.click();
    URL.revokeObjectURL(url);
  } catch {
    error.value = "No se pudo generar la plantilla. Probá de nuevo.";
  }
}

function alElegirArchivo(archivo: File | null): void {
  archivoElegido.value = archivo;
}

async function subir(): Promise<void> {
  if (!seccionElegida.value || !archivoElegido.value) return;
  subiendo.value = true;
  error.value = "";
  resultado.value = null;
  try {
    resultado.value = await subirPlantillaAsistencia({
      section: seccionElegida.value,
      date: fecha.value,
      file: archivoElegido.value,
    });
  } catch {
    error.value = "No se pudo subir la plantilla. Probá de nuevo.";
  } finally {
    subiendo.value = false;
  }
}

onMounted(cargar);
</script>

<template>
  <section class="plantilla-asistencia">
    <PageHeader titulo="Plantilla de asistencia de talleres" />

    <ErrorBanner v-if="error" :mensaje="error" etiqueta-accion="Reintentar" @accion="cargar" />
    <CargandoBloque v-else-if="cargando" />
    <p v-else-if="!puedeUsarPlantilla" class="plantilla-asistencia__nota">
      Esta pantalla es para el taller que tenés a cargo.
    </p>

    <template v-else>
      <div class="plantilla-asistencia__pasos">
        <AppPanel titulo="1. Descargá la plantilla" descripcion="Trae la lista del taller para la fecha que elijas.">
          <div class="plantilla-asistencia__campos">
            <div class="plantilla-asistencia__filtros">
              <FormSelect id="section" etiqueta="Taller" :opciones="opcionesSeccion" v-model="seccionElegida" />
              <FormField id="fecha" etiqueta="Fecha" tipo="date" v-model="fecha" />
            </div>
            <AppButton variante="secundario" :deshabilitado="!seccionElegida" @click="descargar">
              Descargar plantilla
            </AppButton>
          </div>
        </AppPanel>

        <AppPanel titulo="2. Subí la plantilla llena" descripcion="Se revisa completa antes de guardar nada.">
          <div class="plantilla-asistencia__campos">
            <CampoArchivo id="file" etiqueta="Archivo de Excel (.xlsx)" accept=".xlsx" @elegir="alElegirArchivo" />
            <AppButton :deshabilitado="!archivoElegido || subiendo" @click="subir">
              {{ subiendo ? "Subiendo…" : "Subir plantilla" }}
            </AppButton>
          </div>
        </AppPanel>
      </div>

      <p v-if="resultado?.creados !== undefined" class="plantilla-asistencia__exito">
        Se registraron {{ resultado.creados }} asistencias.
      </p>

      <div v-if="resultado?.errores?.length" class="plantilla-asistencia__errores" role="alert">
        <p>La plantilla tiene errores y no se guardó ningún registro. Corregí estas filas y volvé a subirla:</p>
        <ul>
          <li v-for="(err, indice) in resultado.errores" :key="indice">{{ err }}</li>
        </ul>
      </div>
    </template>
  </section>
</template>

<style scoped>
.plantilla-asistencia__nota {
  color: var(--color-tinta-suave);
}

.plantilla-asistencia__pasos {
  display: grid;
  gap: var(--espacio-lg);
  align-items: start;
}

.plantilla-asistencia__campos {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--espacio-lg);
}

.plantilla-asistencia__campos > :not(button) {
  align-self: stretch;
}

.plantilla-asistencia__filtros {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 12rem), 1fr));
  gap: var(--espacio-md);
}

.plantilla-asistencia__exito {
  color: var(--color-exito);
  font-weight: 600;
}

.plantilla-asistencia__errores {
  padding: var(--espacio-lg);
  background: var(--color-etiqueta-alerta-fondo);
  color: var(--color-etiqueta-alerta-texto);
  border-left: 4px solid var(--color-peligro);
  border-radius: var(--radio-md);
}

.plantilla-asistencia__errores p {
  margin: 0 0 var(--espacio-sm);
  font-weight: 600;
}

.plantilla-asistencia__errores ul {
  margin: 0;
  padding-left: var(--espacio-xl);
}

@media (min-width: 64rem) {
  .plantilla-asistencia__pasos {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
