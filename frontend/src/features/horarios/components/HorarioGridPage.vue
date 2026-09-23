<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";

import { assignmentsApi, listarUsuariosPorRoles } from "@/features/asignaciones/api/asignacionesApi";
import { AppButton, AppModal, ErrorBanner, FormSelect } from "@/shared/components";
import type { components } from "@/shared/types/api";
import type { ScheduleBlock, TeacherAssignment } from "@/shared/types/models";

import { DIAS, PERIODOS, scheduleBlocksApi } from "../api/horariosApi";

type Usuario = components["schemas"]["User"];

const cargando = ref(true);
const error = ref("");
const asignaciones = ref<TeacherAssignment[]>([]);
const bloques = ref<ScheduleBlock[]>([]);
const personas = ref<Usuario[]>([]);

const docenteElegido = ref("");

// Un docente puede aparecer en varias asignaciones (varios cursos o
// secciones) — el selector es por persona, no por asignación, para
// poder armar toda su semana en una sola grilla.
const opcionesDocente = computed(() => {
  const vistos = new Set<string>();
  const opciones: { valor: string; etiqueta: string }[] = [];
  for (const a of asignaciones.value) {
    if (vistos.has(a.teacher)) continue;
    vistos.add(a.teacher);
    opciones.push({ valor: a.teacher, etiqueta: nombreDocente(a.teacher) });
  }
  return opciones;
});

function nombreDocente(teacherPublicId: string): string {
  const u = personas.value.find((u) => u.public_id === teacherPublicId);
  return u ? `${u.first_name} ${u.last_name}`.trim() || u.username : teacherPublicId;
}

const misAsignaciones = computed(() =>
  asignaciones.value.filter((a) => a.teacher === docenteElegido.value),
);
const opcionesAsignacion = computed(() =>
  misAsignaciones.value.map((a) => ({
    valor: a.public_id,
    etiqueta: `${a.course_name} — ${a.section_grade} ${a.section_letter}`.trim(),
  })),
);

function bloqueEn(dia: string, periodo: number): ScheduleBlock | undefined {
  const idsPropios = new Set(misAsignaciones.value.map((a) => a.public_id));
  return bloques.value.find(
    (b) => idsPropios.has(b.assignment) && b.day_of_week === dia && b.period_number === periodo,
  );
}
function etiquetaBloque(bloque: ScheduleBlock): string {
  const asignacion = asignaciones.value.find((a) => a.public_id === bloque.assignment);
  return asignacion ? `${asignacion.course_name}` : "—";
}

async function cargar(): Promise<void> {
  cargando.value = true;
  error.value = "";
  try {
    const [asignacionesResp, bloquesResp, docentesResp, talleristasResp] = await Promise.all([
      assignmentsApi.listar(),
      scheduleBlocksApi.listar(),
      listarUsuariosPorRoles(["Docente", "Docente con sección a cargo"]),
      listarUsuariosPorRoles(["Tallerista"]),
    ]);
    asignaciones.value = asignacionesResp.results;
    bloques.value = bloquesResp.results;
    personas.value = [...docentesResp, ...talleristasResp];
    docenteElegido.value = opcionesDocente.value[0]?.valor ?? "";
  } catch {
    error.value = "No se pudo cargar el horario. Probá de nuevo.";
  } finally {
    cargando.value = false;
  }
}

const modalAbierto = ref(false);
const guardando = ref(false);
const celdaElegida = reactive<{ dia: ScheduleBlock["day_of_week"] | ""; periodo: number }>({
  dia: "",
  periodo: 0,
});
const asignacionParaCelda = ref("");

function abrirCelda(dia: ScheduleBlock["day_of_week"], periodo: number): void {
  celdaElegida.dia = dia;
  celdaElegida.periodo = periodo;
  asignacionParaCelda.value = opcionesAsignacion.value[0]?.valor ?? "";
  modalAbierto.value = true;
}

async function guardarBloque(): Promise<void> {
  guardando.value = true;
  error.value = "";
  try {
    await scheduleBlocksApi.crear({
      assignment: asignacionParaCelda.value,
      day_of_week: celdaElegida.dia as ScheduleBlock["day_of_week"],
      period_number: celdaElegida.periodo,
    });
    modalAbierto.value = false;
    await cargar();
  } catch {
    // Si hubo un cruce (otra sesión armó el horario al mismo tiempo,
    // RN-13/HU-06), recargar la grilla ya muestra la celda ocupada de
    // verdad, en vez de intentar adivinar el mensaje del backend.
    error.value =
      "No se pudo guardar — puede que este docente ya tenga una clase asignada ese día y período. Se actualizó la grilla.";
    await cargar();
  } finally {
    guardando.value = false;
  }
}

async function quitarBloque(bloque: ScheduleBlock): Promise<void> {
  if (!confirm("¿Quitar esta clase del horario?")) return;
  await scheduleBlocksApi.darDeBaja(bloque.public_id);
  await cargar();
}

onMounted(cargar);
</script>

<template>
  <section class="horario-grid">
    <h1>Horario</h1>

    <ErrorBanner v-if="error" :mensaje="error" etiqueta-accion="Reintentar" @accion="cargar" />
    <p v-else-if="cargando">Cargando…</p>

    <template v-else>
      <FormSelect
        id="teacher"
        etiqueta="Docente o tallerista"
        :opciones="opcionesDocente"
        v-model="docenteElegido"
      />

      <table v-if="docenteElegido" class="horario-grid__tabla">
        <thead>
          <tr>
            <th></th>
            <th v-for="dia in DIAS" :key="dia.valor">{{ dia.etiqueta }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="periodo in PERIODOS" :key="periodo.numero">
            <th class="horario-grid__hora">P{{ periodo.numero }}<br /><small>{{ periodo.horario }}</small></th>
            <td v-for="dia in DIAS" :key="dia.valor">
              <template v-if="bloqueEn(dia.valor, periodo.numero)">
                <div class="horario-grid__celda horario-grid__celda--ocupada">
                  {{ etiquetaBloque(bloqueEn(dia.valor, periodo.numero)!) }}
                  <button
                    type="button"
                    class="horario-grid__quitar"
                    aria-label="Quitar"
                    @click="quitarBloque(bloqueEn(dia.valor, periodo.numero)!)"
                  >
                    ✕
                  </button>
                </div>
              </template>
              <button
                v-else
                type="button"
                class="horario-grid__celda horario-grid__celda--vacia"
                @click="abrirCelda(dia.valor, periodo.numero)"
              >
                +
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </template>

    <AppModal v-if="modalAbierto" titulo="Agregar clase" @cerrar="modalAbierto = false">
      <form class="horario-grid__formulario" @submit.prevent="guardarBloque">
        <p>{{ DIAS.find((d) => d.valor === celdaElegida.dia)?.etiqueta }}, período {{ celdaElegida.periodo }}</p>
        <FormSelect
          id="assignment"
          etiqueta="Curso y sección"
          :opciones="opcionesAsignacion"
          v-model="asignacionParaCelda"
        />
        <AppButton tipo="submit" :deshabilitado="guardando">
          {{ guardando ? "Guardando…" : "Guardar" }}
        </AppButton>
      </form>
    </AppModal>
  </section>
</template>

<style scoped>
.horario-grid h1 {
  font-family: var(--fuente-titulo);
  font-size: var(--texto-md);
  margin: 0 0 var(--espacio-xl);
}

.horario-grid__tabla {
  border-collapse: collapse;
  width: 100%;
  margin-top: var(--espacio-xl);
}

.horario-grid__tabla th,
.horario-grid__tabla td {
  border: 1px solid var(--color-linea);
  padding: var(--espacio-xs);
  text-align: center;
  font-size: var(--texto-sm);
}

.horario-grid__hora {
  white-space: nowrap;
  color: var(--color-tinta-suave);
  font-weight: 600;
}

.horario-grid__celda {
  min-height: var(--area-tactil-minima);
  width: 100%;
  border: none;
  border-radius: var(--radio-sm);
  cursor: pointer;
  font-family: var(--fuente-cuerpo);
}

.horario-grid__celda--vacia {
  background: var(--color-fondo);
  color: var(--color-tinta-suave);
}

.horario-grid__celda--ocupada {
  background: var(--color-etiqueta-hoy-fondo);
  color: var(--color-etiqueta-hoy-texto);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--espacio-xs);
  padding: 0.2rem 0.4rem;
}

.horario-grid__quitar {
  background: none;
  border: none;
  cursor: pointer;
  color: inherit;
}

.horario-grid__formulario {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-lg);
}
</style>
