<script setup lang="ts">
import { ChevronLeft, ChevronRight } from "lucide-vue-next";
import { computed, onMounted, ref, watch } from "vue";

import { CargandoBloque, DataTable, EmptyState, ErrorBanner, FormSelect, PageHeader } from "@/shared/components";
import type { ColumnaTabla } from "@/shared/components/DataTable.vue";
import type { AccessLog, AuditLog, Usuario } from "@/shared/types/models";

import { listarAccesos, listarBitacora, TAMANO_PAGINA_BITACORA, usuariosApi } from "../api/usuariosApi";

type Pestana = "cambios" | "accesos";

const pestana = ref<Pestana>("cambios");
const pagina = ref(1);
const total = ref(0);
const cargando = ref(true);
const error = ref("");
const cambios = ref<AuditLog[]>([]);
const accesos = ref<AccessLog[]>([]);
const usuarios = ref<Usuario[]>([]);
const usuarioFiltro = ref("");

const formatoFecha = new Intl.DateTimeFormat("es-GT", { dateStyle: "medium", timeStyle: "short" });

// Nombres de entidad tal como los escribe cada servicio del backend.
const ENTIDADES: Record<string, string> = {
  "accounts.User": "Usuario",
  "students.Student": "Estudiante",
  "attendance.Attendance": "Asistencia",
  "attendance.Justification": "Justificación",
  "grading.Grade": "Nota",
  "grading.Activity": "Actividad",
  "grading.GradeChangeRequest": "Solicitud de corrección",
  "grading.ReportCard": "Boletín",
  Payment: "Pago",
};
const ACCIONES: Record<string, string> = { crear: "Creó", actualizar: "Cambió", eliminar: "Dio de baja" };

// Nombres de campo tal como los guarda cada servicio, en palabras.
const CAMPOS: Record<string, string> = {
  first_name: "nombres",
  last_name: "apellidos",
  email: "correo",
  role: "rol",
  is_active: "cuenta activa",
  username: "usuario",
  accion: "acción",
  period_month: "mes",
  period_year: "año",
  amount: "monto",
  payment_date: "fecha de pago",
  receipt_number: "recibo",
  status: "estado",
  score: "nota",
  current_score: "nota",
  raw_score: "nota",
  original_score: "nota vigente",
  requested_score: "nota propuesta",
  reason: "motivo",
  resolution_note: "respuesta de Dirección",
  resolution: "resolución",
  date: "fecha",
  unidad: "unidad",
  source: "origen",
  name: "nombre",
  activity_type: "tipo",
  max_score: "punteo máximo",
  due_date: "fecha de entrega",
  check_in_time: "hora de llegada",
};

const PATRON_UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function valorLegible(valor: unknown): string {
  if (valor === null || valor === undefined || valor === "") return "vacío";
  if (typeof valor === "boolean") return valor ? "sí" : "no";
  if (valor === "restablecer_contrasena") return "restablecer contraseña";
  return String(valor);
}

/** "rol: Docente → Guía; cuenta activa: sí → no" — qué cambió, en una
 * línea. Los identificadores internos (UUID de la inscripción, etc.) no le
 * dicen nada a quien lee y se omiten. */
function resumen(registro: AuditLog): string {
  const nuevo = (registro.new_value ?? {}) as Record<string, unknown>;
  const anterior = (registro.old_value ?? {}) as Record<string, unknown>;
  return Object.keys(nuevo)
    .filter((campo) => !(typeof nuevo[campo] === "string" && PATRON_UUID.test(nuevo[campo] as string)))
    .map((campo) => {
      const nombre = CAMPOS[campo] ?? campo.replace(/_/g, " ");
      return campo in anterior
        ? `${nombre}: ${valorLegible(anterior[campo])} → ${valorLegible(nuevo[campo])}`
        : `${nombre}: ${valorLegible(nuevo[campo])}`;
    })
    .join("; ");
}

const columnasCambios: ColumnaTabla<AuditLog>[] = [
  { clave: "created_at", etiqueta: "Fecha", ordenable: false },
  { clave: "usuario", etiqueta: "Quién", ordenable: false },
  { clave: "action", etiqueta: "Qué hizo", ordenable: false },
  { clave: "detalle", etiqueta: "Detalle", ordenable: false, completa: true },
];
const columnasAccesos: ColumnaTabla<AccessLog>[] = [
  { clave: "accessed_at", etiqueta: "Fecha", ordenable: false },
  { clave: "usuario", etiqueta: "Quién", ordenable: false },
  { clave: "screen_viewed", etiqueta: "Qué consultó", ordenable: false, completa: true },
];

const opcionesUsuario = computed(() => [
  { valor: "", etiqueta: "Todas las personas" },
  ...usuarios.value.map((u) => ({
    valor: u.public_id,
    etiqueta: [u.first_name, u.last_name].filter(Boolean).join(" ") || u.username,
  })),
]);

const totalPaginas = computed(() => Math.max(1, Math.ceil(total.value / TAMANO_PAGINA_BITACORA)));
const rango = computed(() => {
  if (total.value === 0) return "";
  const desde = (pagina.value - 1) * TAMANO_PAGINA_BITACORA + 1;
  const hasta = Math.min(pagina.value * TAMANO_PAGINA_BITACORA, total.value);
  return `${desde}–${hasta} de ${total.value}`;
});

async function cargar(): Promise<void> {
  cargando.value = true;
  error.value = "";
  try {
    if (pestana.value === "cambios") {
      const respuesta = await listarBitacora(pagina.value);
      cambios.value = respuesta.results;
      total.value = respuesta.count;
    } else {
      const respuesta = await listarAccesos(pagina.value, usuarioFiltro.value);
      accesos.value = respuesta.results;
      total.value = respuesta.count;
    }
  } catch {
    error.value = "No se pudo cargar la bitácora. Inténtalo de nuevo.";
  } finally {
    cargando.value = false;
  }
}

watch([pestana, usuarioFiltro], () => {
  pagina.value = 1;
  cargar();
});
watch(pagina, cargar);

onMounted(async () => {
  cargar();
  try {
    usuarios.value = (await usuariosApi.listar()).results;
  } catch {
    // Sin la lista, el filtro por persona queda en "Todas": la bitácora se
    // sigue viendo.
  }
});
</script>

<template>
  <section class="bitacora-page">
    <PageHeader
      titulo="Bitácora"
      descripcion="Quién cambió notas, pagos, asistencia y cuentas, y quién consultó qué pantalla."
    />

    <div class="bitacora-page__pestanas" role="tablist" aria-label="Qué registro ver">
      <button
        v-for="opcion in [
          { valor: 'cambios', etiqueta: 'Cambios' },
          { valor: 'accesos', etiqueta: 'Accesos' },
        ] as const"
        :key="opcion.valor"
        type="button"
        role="tab"
        class="bitacora-page__pestana"
        :class="{ 'bitacora-page__pestana--activa': pestana === opcion.valor }"
        :aria-selected="pestana === opcion.valor"
        @click="pestana = opcion.valor"
      >
        {{ opcion.etiqueta }}
      </button>
    </div>

    <div v-if="pestana === 'accesos'" class="bitacora-page__filtro">
      <FormSelect id="filtro-persona" etiqueta="Persona" :opciones="opcionesUsuario" v-model="usuarioFiltro" />
    </div>

    <ErrorBanner v-if="error" :mensaje="error" etiqueta-accion="Reintentar" @accion="cargar" />
    <CargandoBloque v-else-if="cargando" :filas="6" />
    <EmptyState
      v-else-if="total === 0"
      titulo="Todavía no hay registros"
      descripcion="Aquí van a aparecer los cambios y las consultas a medida que se use el sistema."
    />

    <template v-else>
      <DataTable
        v-if="pestana === 'cambios'"
        :columnas="columnasCambios"
        :filas="cambios"
        :por-pagina="0"
        descripcion="Bitácora de cambios"
      >
        <template #celda-created_at="{ fila }">{{ formatoFecha.format(new Date(fila.created_at)) }}</template>
        <template #celda-action="{ fila }">
          {{ ACCIONES[fila.action] ?? fila.action }} {{ (ENTIDADES[fila.entity_name] ?? fila.entity_name).toLowerCase() }}
        </template>
        <template #celda-detalle="{ fila }">
          <span class="bitacora-page__detalle">{{ resumen(fila) }}</span>
        </template>
      </DataTable>

      <DataTable v-else :columnas="columnasAccesos" :filas="accesos" :por-pagina="0" descripcion="Registro de accesos">
        <template #celda-accessed_at="{ fila }">{{ formatoFecha.format(new Date(fila.accessed_at)) }}</template>
        <template #celda-screen_viewed="{ fila }">
          {{ fila.pantalla }}
        </template>
      </DataTable>

      <nav v-if="totalPaginas > 1" class="bitacora-page__paginacion" aria-label="Páginas de la bitácora">
        <span class="bitacora-page__rango">{{ rango }}</span>
        <div class="bitacora-page__botones">
          <button type="button" :disabled="pagina === 1" aria-label="Página anterior" @click="pagina--">
            <ChevronLeft aria-hidden="true" />
          </button>
          <button type="button" :disabled="pagina === totalPaginas" aria-label="Página siguiente" @click="pagina++">
            <ChevronRight aria-hidden="true" />
          </button>
        </div>
      </nav>
    </template>
  </section>
</template>

<style scoped>
.bitacora-page__pestanas {
  display: inline-flex;
  gap: var(--espacio-2xs);
  padding: var(--espacio-2xs);
  margin-bottom: var(--espacio-lg);
  background: var(--color-hover);
  border-radius: var(--radio-md);
}

.bitacora-page__pestana {
  min-height: 2.5rem;
  min-width: 7rem;
  padding: 0 var(--espacio-lg);
  background: none;
  border: none;
  border-radius: var(--radio-sm);
  font-weight: 600;
  font-size: var(--texto-sm);
  color: var(--color-tinta-suave);
  cursor: pointer;
}

.bitacora-page__pestana--activa {
  background: var(--color-papel);
  color: var(--color-tinta);
  box-shadow: 0 1px 2px rgb(20 24 28 / 12%);
}

.bitacora-page__filtro {
  max-width: 20rem;
  margin-bottom: var(--espacio-lg);
}

.bitacora-page__detalle {
  color: var(--color-tinta-suave);
  overflow-wrap: anywhere;
}

.bitacora-page__paginacion {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--espacio-md);
  margin-top: var(--espacio-md);
}

.bitacora-page__rango {
  font-size: var(--texto-sm);
  color: var(--color-tinta-suave);
  font-variant-numeric: tabular-nums;
}

.bitacora-page__botones {
  display: flex;
  gap: var(--espacio-xs);
}

.bitacora-page__botones button {
  display: grid;
  place-items: center;
  width: var(--area-tactil-minima);
  height: var(--area-tactil-minima);
  background: var(--color-papel);
  border: 1px solid var(--color-linea);
  border-radius: var(--radio-md);
  cursor: pointer;
}

.bitacora-page__botones button:disabled {
  color: var(--color-linea-fuerte);
  cursor: not-allowed;
}

.bitacora-page__botones svg {
  width: 1.2rem;
  height: 1.2rem;
}
</style>
