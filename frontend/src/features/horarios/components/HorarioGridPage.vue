<script setup lang="ts">
import { X } from "lucide-vue-next";
import { computed, onMounted, reactive, ref } from "vue";

import { assignmentsApi, listarUsuariosPorRoles } from "@/features/asignaciones/api/asignacionesApi";
import { mensajeDelServidor } from "@/shared/api/errores";
import { opcional } from "@/shared/api/opcional";
import { AppButton, AppModal, CargandoBloque, ErrorBanner, FormSelect, PageHeader } from "@/shared/components";
import { avisar } from "@/shared/composables/useAvisos";
import { confirmar } from "@/shared/composables/useConfirmar";
import { usePermisos } from "@/shared/permisos";
import type { components } from "@/shared/types/api";
import type { ScheduleBlock, TeacherAssignment } from "@/shared/types/models";

import { DIAS, PERIODOS, scheduleBlocksApi } from "../api/horariosApi";

type Usuario = components["schemas"]["User"];

// Armar el horario es "editar" en Horarios (Dirección); Coordinación y
// Administrador ven la grilla sin los botones.
const permisos = usePermisos();
const puedeEditar = computed(() => permisos.puedeEditar("horarios_calendario"));

const cargando = ref(true);
const error = ref("");
const errorModal = ref("");
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
    opciones.push({ valor: a.teacher, etiqueta: nombreDocente(a.teacher, a.teacher_name) });
  }
  return opciones;
});

function nombreDocente(teacherPublicId: string, respaldo = ""): string {
  const u = personas.value.find((u) => u.public_id === teacherPublicId);
  return u ? `${u.first_name} ${u.last_name}`.trim() || u.username : respaldo || teacherPublicId;
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
      opcional(listarUsuariosPorRoles(["Docente", "Docente con sección a cargo"]), []),
      opcional(listarUsuariosPorRoles(["Tallerista"]), []),
    ]);
    asignaciones.value = asignacionesResp.results;
    bloques.value = bloquesResp.results;
    personas.value = [...docentesResp, ...talleristasResp];
    // No resetear si la persona elegida sigue teniendo asignaciones: esto
    // se vuelve a llamar después de guardar un bloque (para reflejar la
    // celda recién ocupada), y perder la selección ahí saltaría al
    // horario de otra persona sin avisar.
    if (!opcionesDocente.value.some((o) => o.valor === docenteElegido.value)) {
      docenteElegido.value = opcionesDocente.value[0]?.valor ?? "";
    }
  } catch {
    error.value = "No se pudo cargar el horario. Inténtalo de nuevo.";
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
  errorModal.value = "";
  modalAbierto.value = true;
}

async function guardarBloque(): Promise<void> {
  guardando.value = true;
  errorModal.value = "";
  try {
    await scheduleBlocksApi.crear({
      assignment: asignacionParaCelda.value,
      day_of_week: celdaElegida.dia as ScheduleBlock["day_of_week"],
      period_number: celdaElegida.periodo,
    });
    modalAbierto.value = false;
    await cargar();
  } catch (e) {
    // Si hubo un cruce (otra sesión armó el horario al mismo tiempo,
    // RN-13/HU-06), recargar la grilla ya muestra la celda ocupada de
    // verdad, en vez de intentar adivinar el mensaje del backend.
    errorModal.value = mensajeDelServidor(e, "No se pudo guardar — puede que este docente ya tenga una clase asignada ese día y período. Se actualizó la grilla.");
    await cargar();
  } finally {
    guardando.value = false;
  }
}

async function quitarBloque(bloque: ScheduleBlock): Promise<void> {
  const confirmado = await confirmar({
    titulo: "¿Quitar esta clase del horario?",
    etiquetaConfirmar: "Quitar clase",
    peligro: true,
  });
  if (!confirmado) return;
  try {
    await scheduleBlocksApi.darDeBaja(bloque.public_id);
    avisar("Clase quitada del horario.");
    await cargar();
  } catch {
    avisar("No se pudo quitar la clase. Inténtalo de nuevo.", "error");
  }
}

onMounted(cargar);
</script>

<template>
  <section class="horario-grid">
    <PageHeader titulo="Horario" descripcion="Elige a la persona para ver o armar su semana de clases." />

    <ErrorBanner v-if="error" :mensaje="error" etiqueta-accion="Reintentar" @accion="cargar" />
    <CargandoBloque v-else-if="cargando" />

    <template v-else>
      <FormSelect
        id="teacher"
        etiqueta="Docente o tallerista"
        :opciones="opcionesDocente"
        v-model="docenteElegido"
      />

      <!-- Seis columnas no caben en un teléfono: la grilla se desliza de
           lado dentro de su marco, sin mover el resto de la página. -->
      <div v-if="docenteElegido" class="horario-grid__marco">
      <table class="horario-grid__tabla">
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
                    v-if="puedeEditar"
                    type="button"
                    class="horario-grid__quitar"
                    aria-label="Quitar"
                    @click="quitarBloque(bloqueEn(dia.valor, periodo.numero)!)"
                  >
                    <X aria-hidden="true" />
                  </button>
                </div>
              </template>
              <span v-else-if="!puedeEditar" class="horario-grid__libre">Libre</span>
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
      </div>
    </template>

    <AppModal v-if="modalAbierto" titulo="Agregar clase" @cerrar="modalAbierto = false">
      <ErrorBanner v-if="errorModal" :mensaje="errorModal" />
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
.horario-grid__marco {
  overflow-x: auto;
  background: var(--color-papel);
  border: 1px solid var(--color-linea);
  border-radius: var(--radio-lg);
}

.horario-grid__tabla {
  border-collapse: collapse;
  width: 100%;
  min-width: 40rem;
  table-layout: fixed;
}

.horario-grid__tabla th,
.horario-grid__tabla td {
  border-bottom: 1px solid var(--color-linea);
  border-right: 1px solid var(--color-linea);
  padding: var(--espacio-xs);
  text-align: center;
  vertical-align: middle;
  font-size: var(--texto-sm);
}

.horario-grid__tabla tr > :last-child {
  border-right: none;
}

.horario-grid__tabla tbody tr:last-child > * {
  border-bottom: none;
}

.horario-grid__tabla thead th {
  padding: var(--espacio-sm) var(--espacio-xs);
  font-weight: 600;
  color: var(--color-tinta-suave);
}

.horario-grid__tabla th:first-child {
  width: 6.5rem;
}

.horario-grid__hora {
  white-space: nowrap;
  color: var(--color-tinta-suave);
  font-weight: 600;
  line-height: 1.3;
}

.horario-grid__hora small {
  font-weight: 400;
  font-variant-numeric: tabular-nums;
}

.horario-grid__celda {
  min-height: var(--area-tactil-minima);
  width: 100%;
  border: none;
  border-radius: var(--radio-sm);
  font-family: var(--fuente-cuerpo);
  font-size: var(--texto-sm);
}

.horario-grid__celda--vacia {
  background: var(--color-fondo);
  color: var(--color-tinta-suave);
  font-size: var(--texto-md);
  cursor: pointer;
}

.horario-grid__celda--vacia:hover {
  background: var(--color-accion-suave);
  color: var(--color-accion);
}

.horario-grid__celda--ocupada {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--espacio-2xs);
  padding: var(--espacio-xs) var(--espacio-xs) var(--espacio-xs) var(--espacio-sm);
  background: var(--color-etiqueta-hoy-fondo);
  color: var(--color-etiqueta-hoy-texto);
  text-align: left;
  line-height: 1.3;
}

.horario-grid__libre {
  color: var(--color-linea-fuerte);
  font-size: var(--texto-xs);
}

.horario-grid__quitar {
  flex: none;
  display: grid;
  place-items: center;
  width: 2rem;
  height: 2rem;
  background: none;
  border: none;
  border-radius: var(--radio-sm);
  color: inherit;
  cursor: pointer;
}

.horario-grid__quitar:hover {
  background: rgb(255 255 255 / 60%);
}

.horario-grid__quitar svg {
  width: 1rem;
  height: 1rem;
}

.horario-grid__formulario {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-lg);
}
</style>
