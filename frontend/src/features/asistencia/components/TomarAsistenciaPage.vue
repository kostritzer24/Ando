<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";

import { assignmentsApi } from "@/features/asignaciones/api/asignacionesApi";
import { seccionesApi } from "@/features/catalogo/api/catalogoApi";
import { enrollmentsApi, studentsApi } from "@/features/estudiantes/api/estudiantesApi";
import { CargandoBloque, ErrorBanner, FormSelect, PageHeader } from "@/shared/components";
import { usePermisos } from "@/shared/permisos";
import type { Attendance, Enrollment, Section, Student, TeacherAssignment } from "@/shared/types/models";

import { attendanceApi, registrarAsistencia } from "../api/asistenciaApi";

const ESTADOS = [
  { valor: "presente", etiqueta: "Presente" },
  { valor: "tarde", etiqueta: "Tarde" },
  { valor: "ausente", etiqueta: "Ausente" },
  { valor: "justificado", etiqueta: "Justificado" },
] as const;

const cargando = ref(true);
const error = ref("");
const asignaciones = ref<TeacherAssignment[]>([]);
const secciones = ref<Section[]>([]);
const estudiantes = ref<Student[]>([]);

const seccionElegida = ref("");
const fecha = ref(new Date().toISOString().slice(0, 10));

const inscripciones = ref<Enrollment[]>([]);
const asistenciasDelDia = ref<Attendance[]>([]);
const cargandoRoster = ref(false);
const guardandoPorEstudiante = ref<Record<string, boolean>>({});

// Quien alcanza Datos maestros (Dirección, Coordinación, Administrador)
// ve todas las secciones; un docente, solo las de sus asignaciones.
// Marcar es "editar" en Asistencia: Coordinación y Administrador solo
// consultan lo que ya se registró.
const permisos = usePermisos();
const veTodasLasSecciones = computed(() => permisos.puedeVer("datos_maestros"));
const soloLectura = computed(() => !permisos.puedeEditar("asistencia"));

// `/sections/` vive detrás del área "datos_maestros", a la que un
// docente no llega (docs/permisos-roles.md) — para el resto de roles,
// la lista de secciones sale de las propias asignaciones (que ya traen
// el grado/letra/tipo de la sección, sección 14.2: nunca se le abre a
// un docente más catálogo del que necesita). RN footnote 4: Dirección
// registra asistencia matutina aunque el módulo viva en el portal
// operativo, y no tiene asignaciones propias — a ella sí se le muestran
// todas las secciones.
const opcionesSeccion = computed(() => {
  if (veTodasLasSecciones.value) {
    return secciones.value.map((s) => ({
      valor: s.public_id,
      etiqueta: `${s.grade} ${s.letter}`.trim() + (s.type === "taller" ? " (taller)" : ""),
    }));
  }
  const vistas = new Set<string>();
  const opciones: { valor: string; etiqueta: string }[] = [];
  for (const asignacion of asignaciones.value) {
    if (vistas.has(asignacion.section)) continue;
    vistas.add(asignacion.section);
    opciones.push({
      valor: asignacion.section,
      etiqueta:
        `${asignacion.section_grade} ${asignacion.section_letter}`.trim() +
        (asignacion.section_type === "taller" ? " (taller)" : ""),
    });
  }
  return opciones;
});

function nombreEstudiante(studentPublicId: string): string {
  const est = estudiantes.value.find((e) => e.public_id === studentPublicId);
  return est ? `${est.first_name} ${est.last_name}` : "—";
}

function asistenciaDe(inscripcion: Enrollment): Attendance | undefined {
  return asistenciasDelDia.value.find((a) => a.enrollment === inscripcion.public_id);
}

async function cargarBase(): Promise<void> {
  cargando.value = true;
  error.value = "";
  try {
    const [asignacionesResp, estudiantesResp] = await Promise.all([
      assignmentsApi.listar(),
      studentsApi.listar(),
    ]);
    asignaciones.value = asignacionesResp.results;
    estudiantes.value = estudiantesResp.results;
    if (veTodasLasSecciones.value) {
      secciones.value = (await seccionesApi.listar()).results;
    }
    seccionElegida.value = opcionesSeccion.value[0]?.valor ?? "";
  } catch {
    error.value = "No se pudo cargar la información inicial. Probá de nuevo.";
  } finally {
    cargando.value = false;
  }
}

async function cargarRoster(): Promise<void> {
  if (!seccionElegida.value) {
    inscripciones.value = [];
    asistenciasDelDia.value = [];
    return;
  }
  cargandoRoster.value = true;
  error.value = "";
  try {
    const [inscripcionesResp, asistenciasResp] = await Promise.all([
      enrollmentsApi.listar(),
      attendanceApi.listar(),
    ]);
    inscripciones.value = inscripcionesResp.results.filter(
      (i) => i.section === seccionElegida.value && i.is_active !== false,
    );
    asistenciasDelDia.value = asistenciasResp.results.filter((a) => a.date === fecha.value);
  } catch {
    error.value = "No se pudo cargar la lista de estudiantes de la sección. Probá de nuevo.";
  } finally {
    cargandoRoster.value = false;
  }
}

async function marcar(inscripcion: Enrollment, estado: Attendance["status"]): Promise<void> {
  guardandoPorEstudiante.value[inscripcion.public_id] = true;
  error.value = "";
  try {
    const existente = asistenciaDe(inscripcion);
    if (existente) {
      const actualizada = await attendanceApi.actualizar(existente.public_id, { status: estado });
      const indice = asistenciasDelDia.value.findIndex((a) => a.public_id === existente.public_id);
      asistenciasDelDia.value[indice] = actualizada;
    } else {
      const creada = await registrarAsistencia({
        enrollment: inscripcion.public_id,
        date: fecha.value,
        status: estado,
      });
      asistenciasDelDia.value.push(creada);
    }
  } catch {
    error.value = "No se pudo guardar la asistencia de ese estudiante. Probá de nuevo.";
  } finally {
    guardandoPorEstudiante.value[inscripcion.public_id] = false;
  }
}

async function marcarPorHoraLlegada(inscripcion: Enrollment, hora: string): Promise<void> {
  if (!hora) return;
  guardandoPorEstudiante.value[inscripcion.public_id] = true;
  error.value = "";
  try {
    const creada = await registrarAsistencia({
      enrollment: inscripcion.public_id,
      date: fecha.value,
      check_in_time: hora,
    });
    asistenciasDelDia.value.push(creada);
  } catch {
    error.value = "No se pudo guardar la hora de llegada de ese estudiante. Probá de nuevo.";
  } finally {
    guardandoPorEstudiante.value[inscripcion.public_id] = false;
  }
}

watch([seccionElegida, fecha], cargarRoster);

onMounted(async () => {
  await cargarBase();
  await cargarRoster();
});
</script>

<template>
  <section class="tomar-asistencia">
    <PageHeader
      :titulo="soloLectura ? 'Asistencia' : 'Tomar asistencia'"
      :descripcion="soloLectura ? 'Consulta de la asistencia registrada por sección y día.' : undefined"
    />

    <ErrorBanner v-if="error" :mensaje="error" etiqueta-accion="Reintentar" @accion="cargarRoster" />
    <CargandoBloque v-else-if="cargando" />

    <template v-else>
      <div class="tomar-asistencia__filtros">
        <FormSelect
          id="section"
          etiqueta="Sección"
          :opciones="opcionesSeccion"
          v-model="seccionElegida"
        />
        <div class="tomar-asistencia__fecha">
          <label for="fecha">Fecha</label>
          <input id="fecha" type="date" v-model="fecha" />
        </div>
      </div>

      <CargandoBloque v-if="cargandoRoster" />
      <p v-else-if="inscripciones.length === 0" class="tomar-asistencia__vacio">
        No hay estudiantes inscritos en esta sección.
      </p>

      <ul v-else class="tomar-asistencia__lista">
        <li v-for="inscripcion in inscripciones" :key="inscripcion.public_id" class="tomar-asistencia__fila">
          <span class="tomar-asistencia__nombre">{{ nombreEstudiante(inscripcion.student) }}</span>
          <span class="tomar-asistencia__botones">
            <button
              v-for="estado in ESTADOS"
              :key="estado.valor"
              type="button"
              class="tomar-asistencia__boton"
              :class="{
                'tomar-asistencia__boton--activo': asistenciaDe(inscripcion)?.status === estado.valor,
              }"
              :disabled="soloLectura || guardandoPorEstudiante[inscripcion.public_id]"
              :aria-pressed="asistenciaDe(inscripcion)?.status === estado.valor"
              @click="marcar(inscripcion, estado.valor)"
            >
              {{ estado.etiqueta }}
            </button>
          </span>
          <span v-if="!soloLectura && !asistenciaDe(inscripcion)" class="tomar-asistencia__hora">
            <label :for="`hora-${inscripcion.public_id}`">o la hora de llegada</label>
            <input
              :id="`hora-${inscripcion.public_id}`"
              type="time"
              :disabled="guardandoPorEstudiante[inscripcion.public_id]"
              @change="marcarPorHoraLlegada(inscripcion, ($event.target as HTMLInputElement).value)"
            />
          </span>
        </li>
      </ul>
      <p v-if="!soloLectura" class="tomar-asistencia__nota">
        Cada estado se guarda apenas lo elegís — podés cerrar esta pantalla y volver más tarde
        para completar el resto. También podés registrar la hora de llegada en vez del estado: el
        sistema decide si cuenta como tarde (RN-11).
      </p>
    </template>
  </section>
</template>

<style scoped>
/* Mobile-first: pasar lista se hace con el teléfono en la mano, parado
   frente al grupo. Cada estudiante es un bloque con su nombre y los
   cuatro estados a lo ancho (áreas táctiles grandes); desde 48rem el
   nombre va a la izquierda y los estados a la derecha. */
.tomar-asistencia__filtros {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: var(--espacio-md);
}

.tomar-asistencia__fecha {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-xs);
}

.tomar-asistencia__fecha label {
  font-size: var(--texto-sm);
  font-weight: 600;
}

.tomar-asistencia__fecha input {
  width: 100%;
  min-height: var(--area-tactil-minima);
  padding: 0 0.75rem;
  border: 1px solid var(--color-borde-campo);
  border-radius: var(--radio-md);
  background: var(--color-papel);
  font-size: var(--texto-base);
}

.tomar-asistencia__vacio {
  color: var(--color-tinta-suave);
}

.tomar-asistencia__lista {
  list-style: none;
  padding: 0;
  margin: 0;
  background: var(--color-papel);
  border: 1px solid var(--color-linea);
  border-radius: var(--radio-lg);
}

.tomar-asistencia__fila {
  display: grid;
  gap: var(--espacio-sm);
  padding: var(--espacio-md) var(--espacio-lg);
}

.tomar-asistencia__fila + .tomar-asistencia__fila {
  border-top: 1px solid var(--color-linea);
}

.tomar-asistencia__nombre {
  font-weight: 600;
}

.tomar-asistencia__botones {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  border: 1px solid var(--color-borde-campo);
  border-radius: var(--radio-md);
  overflow: hidden;
}

.tomar-asistencia__boton {
  min-height: var(--area-tactil-minima);
  padding: 0 var(--espacio-2xs);
  border: none;
  background: var(--color-papel);
  font-size: var(--texto-sm);
  font-weight: 500;
  cursor: pointer;
}

.tomar-asistencia__boton + .tomar-asistencia__boton {
  border-left: 1px solid var(--color-borde-campo);
}

.tomar-asistencia__boton:hover:not(:disabled) {
  background: var(--color-accion-suave);
}

.tomar-asistencia__boton:focus-visible {
  outline-offset: -3px;
}

.tomar-asistencia__boton--activo {
  background: var(--color-accion);
  color: var(--color-papel);
  font-weight: 700;
}

.tomar-asistencia__boton:disabled {
  cursor: default;
}

/* En consulta, lo no elegido se apaga y lo registrado se sigue leyendo. */
.tomar-asistencia__boton:disabled:not(.tomar-asistencia__boton--activo) {
  color: var(--color-tinta-suave);
  background: var(--color-fondo);
}

.tomar-asistencia__hora {
  display: flex;
  align-items: center;
  gap: var(--espacio-sm);
  font-size: var(--texto-sm);
  color: var(--color-tinta-suave);
}

.tomar-asistencia__hora input {
  min-height: 2.5rem;
  padding: 0 0.5rem;
  border: 1px solid var(--color-borde-campo);
  border-radius: var(--radio-sm);
  background: var(--color-papel);
}

.tomar-asistencia__nota {
  color: var(--color-tinta-suave);
  font-size: var(--texto-sm);
  max-width: 60ch;
}

@media (min-width: 40rem) {
  .tomar-asistencia__filtros {
    grid-template-columns: repeat(2, minmax(0, 16rem));
  }
}

@media (min-width: 48rem) {
  .tomar-asistencia__fila {
    grid-template-columns: minmax(0, 1fr) 26rem;
    align-items: center;
    column-gap: var(--espacio-xl);
  }

  .tomar-asistencia__hora {
    grid-column: 2;
    justify-content: flex-end;
  }
}
</style>
