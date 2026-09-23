<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { assignmentsApi } from "@/features/asignaciones/api/asignacionesApi";
import { seccionesApi } from "@/features/catalogo/api/catalogoApi";
import { useAuthStore } from "@/features/auth/stores/authStore";
import { AppButton, ErrorBanner, FormSelect } from "@/shared/components";
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

function alElegirArchivo(evento: Event): void {
  archivoElegido.value = (evento.target as HTMLInputElement).files?.[0] ?? null;
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
    <h1>Plantilla de asistencia de talleres</h1>

    <ErrorBanner v-if="error" :mensaje="error" etiqueta-accion="Reintentar" @accion="cargar" />
    <p v-else-if="cargando">Cargando…</p>
    <p v-else-if="!puedeUsarPlantilla" class="plantilla-asistencia__nota">
      Esta pantalla es para el taller que tenés a cargo.
    </p>

    <template v-else>
      <div class="plantilla-asistencia__filtros">
        <FormSelect id="section" etiqueta="Taller" :opciones="opcionesSeccion" v-model="seccionElegida" />
        <div class="plantilla-asistencia__fecha">
          <label for="fecha">Fecha</label>
          <input id="fecha" type="date" v-model="fecha" />
        </div>
      </div>

      <AppButton variante="secundario" :deshabilitado="!seccionElegida" @click="descargar">
        Descargar plantilla
      </AppButton>

      <div class="plantilla-asistencia__subida">
        <label for="file">Subir plantilla ya llena</label>
        <input id="file" type="file" accept=".xlsx" @change="alElegirArchivo" />
        <AppButton :deshabilitado="!archivoElegido || subiendo" @click="subir">
          {{ subiendo ? "Subiendo…" : "Subir" }}
        </AppButton>
      </div>

      <p v-if="resultado?.creados !== undefined" class="plantilla-asistencia__exito">
        Se registraron {{ resultado.creados }} asistencias.
      </p>

      <div v-if="resultado?.errores?.length" class="plantilla-asistencia__errores">
        <p>La plantilla tiene errores — no se guardó ningún registro todavía:</p>
        <ul>
          <li v-for="(err, indice) in resultado.errores" :key="indice">{{ err }}</li>
        </ul>
      </div>
    </template>
  </section>
</template>

<style scoped>
.plantilla-asistencia h1 {
  font-family: var(--fuente-titulo);
  font-size: var(--texto-md);
  margin: 0 0 var(--espacio-xl);
}

.plantilla-asistencia__nota {
  color: var(--color-tinta-suave);
}

.plantilla-asistencia__filtros {
  display: flex;
  gap: var(--espacio-xl);
  align-items: flex-end;
  margin-bottom: var(--espacio-lg);
  flex-wrap: wrap;
}

.plantilla-asistencia__fecha {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-xs);
}

.plantilla-asistencia__fecha input {
  min-height: var(--area-tactil-minima);
  padding: 0 0.75rem;
  border: 1px solid var(--color-linea);
  border-radius: var(--radio-md);
}

.plantilla-asistencia__subida {
  margin-top: var(--espacio-xl);
  padding-top: var(--espacio-xl);
  border-top: 1px solid var(--color-linea);
  display: flex;
  flex-direction: column;
  gap: var(--espacio-md);
  align-items: flex-start;
}

.plantilla-asistencia__exito {
  color: var(--color-etiqueta-taller-texto);
  margin-top: var(--espacio-lg);
}

.plantilla-asistencia__errores {
  margin-top: var(--espacio-lg);
  background: var(--color-etiqueta-alerta-fondo);
  color: var(--color-etiqueta-alerta-texto);
  border-radius: var(--radio-md);
  padding: var(--espacio-lg);
}
</style>
