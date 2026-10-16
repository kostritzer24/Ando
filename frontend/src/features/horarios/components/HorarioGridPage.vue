<script setup lang="ts">
import { X } from "lucide-vue-next";
import { computed, onMounted, reactive, ref } from "vue";

import { assignmentsApi, listarUsuariosPorRoles } from "@/features/asignaciones/api/asignacionesApi";
import { mensajeDelServidor } from "@/shared/api/errores";
import { opcional } from "@/shared/api/opcional";
import { AppButton, AppModal, CargandoBloque, ErrorBanner, FormBuscador, FormSelect, PageHeader } from "@/shared/components";
import { avisar } from "@/shared/composables/useAvisos";
import { confirmar } from "@/shared/composables/useConfirmar";
import { usePermisos } from "@/shared/permisos";
import type { components } from "@/shared/types/api";
import type { ScheduleBlock, TeacherAssignment } from "@/shared/types/models";

import { descargarArchivo } from "@/features/pagos/api/pagosApi";
import { descargarHorarioPdf } from "@/features/reportes/api/reportesApi";

import { DIAS, PERIODOS, PERIODOS_TALLER, scheduleBlocksApi } from "../api/horariosApi";

type Usuario = components["schemas"]["User"];

// Armar el horario es "editar" en Horarios (Dirección); Coordinación ve la
// grilla sin los botones.
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
  asignaciones.value.filter((a) => a.teacher === docenteElegido.value && a.is_active !== false),
);

// Los cursos de la jornada usan los períodos 1 a 6; los talleres, los 7 a 9
// (la tarde). Cada persona ve la franja que le toca según sus asignaciones.
const periodosVisibles = computed(() => {
  const hayTaller = misAsignaciones.value.some((a) => a.section_type === "taller");
  const hayJornada = misAsignaciones.value.some((a) => a.section_type !== "taller");
  return [...(hayJornada || !hayTaller ? PERIODOS : []), ...(hayTaller ? PERIODOS_TALLER : [])];
});

const esTarde = (periodo: number): boolean => periodo >= 7;

// Bloques vigentes (de asignaciones vigentes): los que de verdad ocupan celdas.
const bloquesVigentes = computed(() => {
  const vigentes = new Set(asignaciones.value.filter((a) => a.is_active !== false).map((a) => a.public_id));
  return bloques.value.filter((b) => b.is_active !== false && vigentes.has(b.assignment));
});

function seccionOcupada(seccion: string, dia: string, periodo: number): boolean {
  const deLaSeccion = new Set(
    asignaciones.value.filter((a) => a.section === seccion).map((a) => a.public_id),
  );
  return bloquesVigentes.value.some(
    (b) => deLaSeccion.has(b.assignment) && b.day_of_week === dia && b.period_number === periodo,
  );
}

// Asignaciones de la persona que sí se pueden poner en esa celda: la franja
// corresponde al tipo de curso y la sección no tiene ya otra clase a esa hora.
function asignacionesLibresEn(dia: string, periodo: number) {
  return misAsignaciones.value.filter(
    (a) => (a.section_type === "taller") === esTarde(periodo) && !seccionOcupada(a.section, dia, periodo),
  );
}

const opcionesAsignacion = computed(() =>
  asignacionesLibresEn(celdaElegida.dia, celdaElegida.periodo).map((a) => ({
    valor: a.public_id,
    etiqueta: `${a.course_name} — ${a.section_grade} ${a.section_letter}`.trim(),
  })),
);

function bloqueEn(dia: string, periodo: number): ScheduleBlock | undefined {
  const idsPropios = new Set(misAsignaciones.value.map((a) => a.public_id));
  return bloquesVigentes.value.find(
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
      opcional(listarUsuariosPorRoles(["Docente"]), []),
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
// Para no repetir el mismo curso día por día: se puede marcar en qué otros
// días va a la misma hora; solo se ofrecen los días en que la persona y la
// sección están libres.
const diasAdicionales = ref<string[]>([]);

function diaLibrePara(dia: string, periodo: number, asignacionId: string): boolean {
  const asignacion = misAsignaciones.value.find((a) => a.public_id === asignacionId);
  if (!asignacion || bloqueEn(dia, periodo)) return false;
  return !seccionOcupada(asignacion.section, dia, periodo);
}

const diasParaRepetir = computed(() =>
  DIAS.filter(
    (d) =>
      d.valor !== celdaElegida.dia &&
      diaLibrePara(d.valor, celdaElegida.periodo, asignacionParaCelda.value),
  ),
);

function alternarDia(valor: string): void {
  diasAdicionales.value = diasAdicionales.value.includes(valor)
    ? diasAdicionales.value.filter((d) => d !== valor)
    : [...diasAdicionales.value, valor];
}

function abrirCelda(dia: ScheduleBlock["day_of_week"], periodo: number): void {
  celdaElegida.dia = dia;
  celdaElegida.periodo = periodo;
  asignacionParaCelda.value = opcionesAsignacion.value[0]?.valor ?? "";
  diasAdicionales.value = [];
  errorModal.value = "";
  modalAbierto.value = true;
}

async function guardarBloque(): Promise<void> {
  guardando.value = true;
  errorModal.value = "";
  try {
    const dias = [celdaElegida.dia, ...diasAdicionales.value.filter((d) => diasParaRepetir.value.some((x) => x.valor === d))];
    for (const dia of dias) {
      await scheduleBlocksApi.crear({
        assignment: asignacionParaCelda.value,
        day_of_week: dia as ScheduleBlock["day_of_week"],
        period_number: celdaElegida.periodo,
      });
    }
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

const descargando = ref(false);
async function descargarPdf(): Promise<void> {
  if (!docenteElegido.value) return;
  descargando.value = true;
  try {
    const { blob, nombreArchivo } = await descargarHorarioPdf({ teacher: docenteElegido.value });
    descargarArchivo(blob, nombreArchivo);
  } catch {
    avisar("No se pudo generar el PDF. Inténtalo de nuevo.", "error");
  } finally {
    descargando.value = false;
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
      <div class="horario-grid__barra">
        <FormBuscador
          id="teacher"
          etiqueta="Docente o tallerista"
          :opciones="opcionesDocente"
          v-model="docenteElegido"
        />
        <AppButton v-if="docenteElegido" variante="secundario" :deshabilitado="descargando" @click="descargarPdf">
          {{ descargando ? "Generando…" : "Descargar horario en PDF" }}
        </AppButton>
      </div>
      <p v-if="puedeEditar && docenteElegido" class="horario-grid__ayuda">
        <span class="horario-grid__muestra horario-grid__muestra--libre"></span> Libre: toca <strong>+</strong> para agregar una clase.
        <span class="horario-grid__muestra horario-grid__muestra--bloqueada"></span> No disponible: la sección ya tiene otra clase a esa hora.
      </p>

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
          <template v-for="periodo in periodosVisibles" :key="periodo.numero">
          <tr v-if="periodo.numero === 4" class="horario-grid__receso">
            <td :colspan="DIAS.length + 1">Receso 10:00–10:40</td>
          </tr>
          <tr>
            <th class="horario-grid__hora">P{{ periodo.numero }}<br /><small>{{ periodo.horario }}</small></th>
            <td v-for="dia in DIAS" :key="dia.valor">
              <template v-if="bloqueEn(dia.valor, periodo.numero)">
                <div class="horario-grid__celda horario-grid__celda--ocupada">
                  <span class="horario-grid__nombre">
                    {{ etiquetaBloque(bloqueEn(dia.valor, periodo.numero)!) }}
                  </span>
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
              <span
                v-else-if="asignacionesLibresEn(dia.valor, periodo.numero).length === 0"
                class="horario-grid__celda horario-grid__celda--bloqueada"
                title="La sección ya tiene otra clase a esa hora"
              >
                No disponible
              </span>
              <button
                v-else
                type="button"
                class="horario-grid__celda horario-grid__celda--vacia"
                aria-label="Agregar clase"
                @click="abrirCelda(dia.valor, periodo.numero)"
              >
                +
              </button>
            </td>
          </tr>
          </template>
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
        <fieldset v-if="diasParaRepetir.length > 0" class="horario-grid__repetir">
          <legend>Repetir a la misma hora el</legend>
          <label v-for="dia in diasParaRepetir" :key="dia.valor">
            <input
              type="checkbox"
              :checked="diasAdicionales.includes(dia.valor)"
              @change="alternarDia(dia.valor)"
            />
            {{ dia.etiqueta }}
          </label>
        </fieldset>
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

.horario-grid__nombre {
  min-width: 0;
  overflow-wrap: anywhere;
}

.horario-grid__tabla tr.horario-grid__receso > td {
  padding: var(--espacio-2xs);
  background: var(--color-fondo);
  color: var(--color-tinta-suave);
  font-size: var(--texto-xs);
  letter-spacing: 0.04em;
  text-transform: uppercase;
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

.horario-grid__barra {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: var(--espacio-md);
}

.horario-grid__barra > :first-child {
  flex: 1 1 18rem;
  max-width: 28rem;
}

.horario-grid__ayuda {
  margin: var(--espacio-sm) 0;
  color: var(--color-tinta-suave);
  font-size: var(--texto-sm);
}

.horario-grid__muestra {
  display: inline-block;
  width: 0.9rem;
  height: 0.9rem;
  margin: 0 0.25rem 0 var(--espacio-sm);
  vertical-align: -0.1rem;
  border-radius: 3px;
}

.horario-grid__muestra--libre {
  background: var(--color-accion-suave);
  border: 1px solid var(--color-accion);
}

.horario-grid__muestra--bloqueada {
  background: repeating-linear-gradient(45deg, var(--color-linea), var(--color-linea) 3px, var(--color-fondo) 3px, var(--color-fondo) 6px);
}

.horario-grid__celda--bloqueada {
  display: grid;
  place-items: center;
  background: repeating-linear-gradient(45deg, var(--color-fondo), var(--color-fondo) 6px, var(--color-hover) 6px, var(--color-hover) 12px);
  color: var(--color-tinta-suave);
  font-size: var(--texto-xs);
  cursor: not-allowed;
}

.horario-grid__celda--vacia {
  background: var(--color-accion-suave);
  color: var(--color-accion);
}

.horario-grid__repetir {
  display: flex;
  flex-wrap: wrap;
  gap: var(--espacio-sm) var(--espacio-lg);
  margin: 0;
  padding: var(--espacio-sm) var(--espacio-md);
  border: 1px solid var(--color-linea);
  border-radius: var(--radio-md);
}

.horario-grid__repetir label {
  display: flex;
  align-items: center;
  gap: var(--espacio-xs);
}

.horario-grid__formulario {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-lg);
}
</style>
