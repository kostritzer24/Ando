<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";

import { becasApi, seccionesApi } from "@/features/catalogo/api/catalogoApi";
import { mensajeDelServidor } from "@/shared/api/errores";
import { opcional } from "@/shared/api/opcional";
import { avisar } from "@/shared/composables/useAvisos";
import { confirmar } from "@/shared/composables/useConfirmar";
import { hoyIso } from "@/shared/fechas";
import { AppButton, CargandoBloque, ErrorBanner, FormSelect } from "@/shared/components";
import type { Enrollment, Scholarship, Section } from "@/shared/types/models";

import { enrollmentsApi } from "../api/estudiantesApi";

/**
 * Inscripciones de un estudiante: su grado, los talleres en que participa
 * y la beca. Cambiar de grado o de taller mueve la misma inscripción —
 * no se vuelve a registrar al estudiante.
 */
const props = defineProps<{ studentPublicId: string; puedeEditar: boolean }>();

const cargando = ref(true);
const error = ref("");
const errorAccion = ref("");
const guardando = ref(false);

const inscripciones = ref<Enrollment[]>([]);
const secciones = ref<Section[]>([]);
const becas = ref<Scholarship[]>([]);

const nuevoTaller = ref("");
const cambio = reactive<{ inscripcion: string; seccion: string }>({ inscripcion: "", seccion: "" });

const delGrado = computed(() => inscripciones.value.filter((i) => i.section_type === "academica"));
const deTalleres = computed(() => inscripciones.value.filter((i) => i.section_type === "taller"));

function nombreSeccion(s: { grade: string; letter?: string | null; cycle_year?: number | null }): string {
  const nombre = `${s.grade} ${s.letter ?? ""}`.trim();
  return s.cycle_year ? `${nombre} (${s.cycle_year})` : nombre;
}

function etiquetaInscripcion(i: Enrollment): string {
  return nombreSeccion({ grade: i.section_grade ?? "", letter: i.section_letter, cycle_year: i.cycle_year });
}

// Secciones del mismo ciclo y tipo, para mover una inscripción.
function destinosPara(inscripcion: Enrollment) {
  return secciones.value
    .filter(
      (s) =>
        s.cycle === inscripcion.cycle &&
        s.type === inscripcion.section_type &&
        s.public_id !== inscripcion.section &&
        s.is_active !== false,
    )
    .map((s) => ({ valor: s.public_id, etiqueta: nombreSeccion(s) }));
}

// Talleres del ciclo del grado en que todavía no participa.
const talleresDisponibles = computed(() => {
  const ciclo = delGrado.value[0]?.cycle;
  const ya = new Set(deTalleres.value.map((i) => i.section));
  return secciones.value
    .filter((s) => s.type === "taller" && s.is_active !== false && s.cycle === ciclo && !ya.has(s.public_id))
    .map((s) => ({ valor: s.public_id, etiqueta: nombreSeccion(s) }));
});

const opcionesBeca = computed(() => [
  { valor: "", etiqueta: "Ninguna" },
  ...becas.value.map((b) => ({ valor: b.public_id, etiqueta: b.name })),
]);

async function cargar(): Promise<void> {
  cargando.value = true;
  error.value = "";
  try {
    const vacio = { count: 0, next: null, previous: null, results: [] };
    const [inscripcionesResp, seccionesResp, becasResp] = await Promise.all([
      enrollmentsApi.listar({ student: props.studentPublicId }),
      opcional(seccionesApi.listar(), vacio),
      opcional(becasApi.listar(), vacio),
    ]);
    inscripciones.value = inscripcionesResp.results.filter((i) => i.is_active !== false);
    secciones.value = seccionesResp.results;
    becas.value = becasResp.results.filter((b) => b.is_active !== false);
    nuevoTaller.value = talleresDisponibles.value[0]?.valor ?? "";
  } catch {
    error.value = "No se pudieron cargar las inscripciones. Inténtalo de nuevo.";
  } finally {
    cargando.value = false;
  }
}

async function ejecutar(accion: () => Promise<void>, exito: string): Promise<void> {
  guardando.value = true;
  errorAccion.value = "";
  try {
    await accion();
    avisar(exito);
    cambio.inscripcion = "";
    await cargar();
  } catch (e) {
    errorAccion.value = mensajeDelServidor(e, "No se pudo guardar el cambio. Inténtalo de nuevo.");
  } finally {
    guardando.value = false;
  }
}

function inscribirEnTaller(): Promise<void> {
  const taller = secciones.value.find((s) => s.public_id === nuevoTaller.value);
  if (!taller) return Promise.resolve();
  return ejecutar(async () => {
    await enrollmentsApi.crear({
      student: props.studentPublicId,
      section: taller.public_id,
      cycle: taller.cycle,
      enrolled_at: hoyIso(),
    });
  }, "Estudiante inscrito en el taller.");
}

function abrirCambio(inscripcion: Enrollment): void {
  cambio.inscripcion = inscripcion.public_id;
  cambio.seccion = destinosPara(inscripcion)[0]?.valor ?? "";
  errorAccion.value = "";
}

function aplicarCambio(inscripcion: Enrollment): Promise<void> {
  return ejecutar(async () => {
    await enrollmentsApi.actualizar(inscripcion.public_id, { section: cambio.seccion });
  }, "Sección actualizada.");
}

function cambiarBeca(inscripcion: Enrollment, valor: string): Promise<void> {
  return ejecutar(async () => {
    await enrollmentsApi.actualizar(inscripcion.public_id, { scholarship: valor || null });
  }, "Beca actualizada.");
}

async function sacarDelTaller(inscripcion: Enrollment): Promise<void> {
  const confirmado = await confirmar({
    titulo: `¿Sacar del taller ${etiquetaInscripcion(inscripcion)}?`,
    mensaje: "Dejará de aparecer en su lista y en la asistencia. Su historial se conserva.",
    etiquetaConfirmar: "Sacar del taller",
    peligro: true,
  });
  if (!confirmado) return;
  await ejecutar(() => enrollmentsApi.darDeBaja(inscripcion.public_id), "Estudiante fuera del taller.");
}

onMounted(cargar);
</script>

<template>
  <section class="inscripciones" aria-labelledby="titulo-inscripciones">
    <h2 id="titulo-inscripciones">Grado y talleres</h2>
    <ErrorBanner v-if="error" :mensaje="error" etiqueta-accion="Reintentar" @accion="cargar" />
    <CargandoBloque v-else-if="cargando" :filas="2" />

    <template v-else>
      <ErrorBanner v-if="errorAccion" :mensaje="errorAccion" />

      <div class="inscripciones__grupo">
        <h3>Grado</h3>
        <p v-if="delGrado.length === 0" class="inscripciones__vacio">Sin inscripción de grado en el ciclo.</p>
        <ul v-else class="inscripciones__lista">
          <li v-for="i in delGrado" :key="i.public_id" class="inscripciones__item">
            <div class="inscripciones__fila">
              <strong>{{ etiquetaInscripcion(i) }}</strong>
              <AppButton
                v-if="puedeEditar && destinosPara(i).length > 0"
                variante="discreto"
                compacto
                @click="abrirCambio(i)"
              >
                Cambiar de sección
              </AppButton>
            </div>
            <form
              v-if="cambio.inscripcion === i.public_id"
              class="inscripciones__cambio"
              @submit.prevent="aplicarCambio(i)"
            >
              <FormSelect
                :id="`cambio-${i.public_id}`"
                etiqueta="Nueva sección"
                :opciones="destinosPara(i)"
                v-model="cambio.seccion"
              />
              <div class="inscripciones__botones">
                <AppButton tipo="submit" :deshabilitado="guardando || !cambio.seccion">Guardar</AppButton>
                <AppButton variante="secundario" @click="cambio.inscripcion = ''">Cancelar</AppButton>
              </div>
            </form>
            <FormSelect
              v-if="puedeEditar"
              :id="`beca-${i.public_id}`"
              etiqueta="Beca"
              :opciones="opcionesBeca"
              :model-value="i.scholarship ?? ''"
              @update:model-value="cambiarBeca(i, $event)"
            />
            <p v-else class="inscripciones__vacio">Beca: {{ i.scholarship ? "Completa" : "Ninguna" }}</p>
          </li>
        </ul>
      </div>

      <div class="inscripciones__grupo">
        <h3>Talleres</h3>
        <p v-if="deTalleres.length === 0" class="inscripciones__vacio">No participa en ningún taller.</p>
        <ul v-else class="inscripciones__lista">
          <li v-for="i in deTalleres" :key="i.public_id" class="inscripciones__item">
            <div class="inscripciones__fila">
              <strong>{{ etiquetaInscripcion(i) }}</strong>
              <AppButton v-if="puedeEditar" variante="discreto" compacto @click="sacarDelTaller(i)">
                Sacar del taller
              </AppButton>
            </div>
          </li>
        </ul>
        <form
          v-if="puedeEditar && talleresDisponibles.length > 0"
          class="inscripciones__cambio"
          @submit.prevent="inscribirEnTaller"
        >
          <FormSelect id="nuevo-taller" etiqueta="Inscribir en un taller" :opciones="talleresDisponibles" v-model="nuevoTaller" />
          <AppButton tipo="submit" :deshabilitado="guardando || !nuevoTaller">Inscribir en el taller</AppButton>
        </form>
      </div>
    </template>
  </section>
</template>

<style scoped>
.inscripciones {
  margin-top: var(--espacio-xl);
  padding-top: var(--espacio-xl);
  border-top: 1px solid var(--color-linea);
  max-width: 28rem;
  display: flex;
  flex-direction: column;
  gap: var(--espacio-lg);
}

.inscripciones h2 {
  font-family: var(--fuente-titulo);
  font-size: var(--texto-base);
  margin: 0;
}

.inscripciones h3 {
  font-size: var(--texto-sm);
  color: var(--color-tinta-suave);
  margin: 0 0 var(--espacio-xs);
}

.inscripciones__grupo {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-sm);
}

.inscripciones__lista {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--espacio-sm);
}

.inscripciones__item {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-sm);
  padding: var(--espacio-md);
  background: var(--color-papel);
  border: 1px solid var(--color-linea);
  border-radius: var(--radio-md);
}

.inscripciones__fila {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--espacio-sm);
  flex-wrap: wrap;
}

.inscripciones__cambio {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-sm);
}

.inscripciones__botones {
  display: flex;
  gap: var(--espacio-sm);
}

.inscripciones__vacio {
  margin: 0;
  color: var(--color-tinta-suave);
  font-size: var(--texto-sm);
}
</style>
