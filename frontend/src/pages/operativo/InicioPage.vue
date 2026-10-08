<script setup lang="ts">
import { ClipboardCheck } from "lucide-vue-next";
import { computed, onMounted, ref } from "vue";

import { useAuthStore } from "@/features/auth/stores/authStore";
import { type BloqueHorarioPropio, DIAS, obtenerMiHorario, PERIODOS } from "@/features/horarios/api/horariosApi";
import { CargandoBloque, ErrorBanner, PageHeader } from "@/shared/components";

const auth = useAuthStore();

const saludo = computed(() => `Hola, ${auth.usuario?.first_name || auth.usuario?.username || ""}`.trim());
const ahora = new Date();
const textoFecha = new Intl.DateTimeFormat("es-GT", { weekday: "long", day: "numeric", month: "long" }).format(ahora);
const fechaHoy = textoFecha.charAt(0).toUpperCase() + textoFecha.slice(1);

// getDay(): 0 = domingo … 6 = sábado; DIAS va de lunes a viernes.
const diaHoy = DIAS[ahora.getDay() - 1]?.valor;

const cargando = ref(true);
const error = ref("");
const bloques = ref<BloqueHorarioPropio[]>([]);

const clasesDeHoy = computed(() =>
  bloques.value
    .filter((b) => b.day_of_week === diaHoy)
    .sort((a, b) => a.period_number - b.period_number)
    .map((b) => ({ ...b, horario: PERIODOS.find((p) => p.numero === b.period_number)?.horario ?? "" })),
);

async function cargar(): Promise<void> {
  cargando.value = true;
  error.value = "";
  try {
    bloques.value = await obtenerMiHorario();
  } catch {
    error.value = "No se pudo cargar tu horario de hoy.";
  } finally {
    cargando.value = false;
  }
}

onMounted(cargar);
</script>

<template>
  <section class="inicio">
    <PageHeader :titulo="saludo" :descripcion="fechaHoy">
      <template #acciones>
        <!-- El camino frecuente en primer plano (sección 15.2): el docente
             entra a pasar lista y llega en un toque. -->
        <RouterLink to="/operativo/asistencia" class="inicio__accion">
          <ClipboardCheck aria-hidden="true" />
          Pasar lista
        </RouterLink>
      </template>
    </PageHeader>

    <section aria-labelledby="titulo-hoy">
      <h2 id="titulo-hoy" class="inicio__subtitulo">Tus clases de hoy</h2>
      <ErrorBanner v-if="error" :mensaje="error" etiqueta-accion="Reintentar" @accion="cargar" />
      <CargandoBloque v-else-if="cargando" :filas="3" />
      <p v-else-if="!diaHoy" class="inicio__vacio">Hoy no hay clases. Tu horario de la semana está en Mi horario.</p>
      <p v-else-if="clasesDeHoy.length === 0" class="inicio__vacio">
        No tienes clases asignadas para hoy en el horario.
      </p>
      <ol v-else class="inicio__clases">
        <li v-for="clase in clasesDeHoy" :key="clase.public_id" class="inicio__clase">
          <span class="inicio__hora">{{ clase.horario }}</span>
          <span class="inicio__curso">
            <span class="inicio__nombre-curso">{{ clase.course }}</span>
            <span class="inicio__seccion">{{ clase.section }}</span>
          </span>
        </li>
      </ol>
    </section>
  </section>
</template>

<style scoped>
.inicio__accion {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--espacio-sm);
  min-height: var(--area-tactil-minima);
  padding: 0 var(--espacio-lg);
  border-radius: var(--radio-md);
  background: var(--color-accion);
  color: var(--color-papel);
  font-weight: 600;
  text-decoration: none;
}

.inicio__accion:hover {
  background: var(--color-accion-hover);
}

.inicio__accion svg {
  width: 1.15em;
  height: 1.15em;
}

.inicio__subtitulo {
  font-size: var(--texto-md);
  margin-bottom: var(--espacio-md);
}

.inicio__vacio {
  margin: 0;
  color: var(--color-tinta-suave);
}

.inicio__clases {
  list-style: none;
  margin: 0;
  padding: 0;
  max-width: 40rem;
  background: var(--color-papel);
  border: 1px solid var(--color-linea);
  border-radius: var(--radio-lg);
}

.inicio__clase {
  display: grid;
  grid-template-columns: 6.5rem 1fr;
  align-items: baseline;
  gap: var(--espacio-md);
  padding: var(--espacio-md) var(--espacio-lg);
}

.inicio__clase + .inicio__clase {
  border-top: 1px solid var(--color-linea);
}

.inicio__hora {
  font-size: var(--texto-sm);
  font-variant-numeric: tabular-nums;
  color: var(--color-tinta-suave);
}

.inicio__curso {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.inicio__nombre-curso {
  font-weight: 600;
}

.inicio__seccion {
  font-size: var(--texto-sm);
  color: var(--color-tinta-suave);
}
</style>
