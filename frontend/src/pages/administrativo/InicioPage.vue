<script setup lang="ts">
import {
  FileBadge,
  FilePen,
  GraduationCap,
  Inbox,
  Megaphone,
  ChartColumn,
  UserCheck,
  UserCog,
  Users,
  Wallet,
} from "lucide-vue-next";
import { computed, onMounted, ref, type Component } from "vue";

import { useAuthStore } from "@/features/auth/stores/authStore";
import { messagesApi } from "@/features/comunicacion/api/comunicacionApi";
import { gradeChangeRequestsApi } from "@/features/notas/api/notasApi";
import { CargandoBloque, ErrorBanner, PageHeader } from "@/shared/components";
import { type Area, usePermisos } from "@/shared/permisos";
import type { GradeChangeRequest, Message } from "@/shared/types/models";

interface Acceso {
  a: string;
  etiqueta: string;
  detalle: string;
  icono: Component;
}

const auth = useAuthStore();
const permisos = usePermisos();

const saludo = computed(() => `Hola, ${auth.usuario?.first_name || auth.usuario?.username || ""}`.trim());
const hoy = new Intl.DateTimeFormat("es-GT", { weekday: "long", day: "numeric", month: "long" }).format(new Date());
const fechaHoy = hoy.charAt(0).toUpperCase() + hoy.slice(1);

// Pendientes: solo lo que espera una decisión de quien entra. Se piden
// solo si el rol puede resolverlos (autorizar cambios de nota, responder
// el buzón), según la matriz de su rol.
const resuelveModificaciones = computed(() => permisos.puedeEditar("modificacion_notas"));
const respondeBuzon = computed(() => permisos.puedeEditar("buzon"));
const muestraPendientes = computed(() => resuelveModificaciones.value || respondeBuzon.value);

const cargando = ref(false);
const error = ref("");
const modificacionesPendientes = ref(0);
const mensajesSinResponder = ref(0);

async function cargarPendientes(): Promise<void> {
  if (!muestraPendientes.value) return;
  cargando.value = true;
  error.value = "";
  try {
    const [solicitudes, mensajes] = await Promise.all([
      resuelveModificaciones.value ? gradeChangeRequestsApi.listar() : Promise.resolve({ results: [] }),
      respondeBuzon.value ? messagesApi.listar() : Promise.resolve({ results: [] }),
    ]);
    modificacionesPendientes.value = (solicitudes.results as GradeChangeRequest[]).filter(
      (s) => s.status === "pendiente",
    ).length;
    mensajesSinResponder.value = (mensajes.results as Message[]).filter((m) => m.status !== "respondido").length;
  } catch {
    error.value = "No se pudieron cargar los pendientes.";
  } finally {
    cargando.value = false;
  }
}

const pendientes = computed(() =>
  [
    {
      a: "/administrativo/notas/modificaciones",
      cantidad: modificacionesPendientes.value,
      texto: (n: number) =>
        n === 1 ? "solicitud de cambio de nota por resolver" : "solicitudes de cambio de nota por resolver",
      icono: FilePen,
    },
    {
      a: "/administrativo/buzon",
      cantidad: mensajesSinResponder.value,
      texto: (n: number) => (n === 1 ? "mensaje de familia sin responder" : "mensajes de familias sin responder"),
      icono: Inbox,
    },
  ].filter((p) => p.cantidad > 0),
);

// Lo más usado, en orden de frecuencia, filtrado por lo que el rol
// alcanza: Encargado de pagos ve Pagos primero, Administrador ve Usuarios.
const CANDIDATOS: (Acceso & { area: Area })[] = [
  { a: "/administrativo/estudiantes", etiqueta: "Estudiantes", detalle: "Expedientes e inscripciones", icono: GraduationCap, area: "estudiantes_encargados" },
  { a: "/administrativo/pagos", etiqueta: "Pagos y solvencia", detalle: "Quién está al día con sus pagos", icono: Wallet, area: "pagos_solvencia" },
  { a: "/administrativo/documentos", etiqueta: "Documentos", detalle: "Constancias y cartas emitidas", icono: FileBadge, area: "documentos" },
  { a: "/administrativo/encargados", etiqueta: "Encargados", detalle: "Familias y sus vínculos", icono: Users, area: "estudiantes_encargados" },
  { a: "/administrativo/usuarios", etiqueta: "Usuarios", detalle: "Cuentas, roles y contraseñas", icono: UserCog, area: "usuarios_roles" },
  { a: "/administrativo/avisos", etiqueta: "Avisos", detalle: "La cartelera de docentes y familias", icono: Megaphone, area: "avisos" },
  { a: "/administrativo/asignaciones", etiqueta: "Asignaciones", detalle: "Quién da cada curso", icono: UserCheck, area: "horarios_calendario" },
  { a: "/administrativo/reportes", etiqueta: "Reportes", detalle: "Reportes institucionales en PDF", icono: ChartColumn, area: "reportes_institucionales" },
];

const accesos = computed(() => CANDIDATOS.filter((c) => permisos.puedeVer(c.area)).slice(0, 5));

onMounted(cargarPendientes);
</script>

<template>
  <section class="inicio">
    <PageHeader :titulo="saludo" :descripcion="fechaHoy" />

    <section v-if="muestraPendientes" class="inicio__bloque" aria-labelledby="titulo-pendientes">
      <h2 id="titulo-pendientes" class="inicio__subtitulo">Pendientes</h2>
      <ErrorBanner v-if="error" :mensaje="error" etiqueta-accion="Reintentar" @accion="cargarPendientes" />
      <CargandoBloque v-else-if="cargando" :filas="2" />
      <p v-else-if="pendientes.length === 0" class="inicio__al-dia">No hay nada esperando tu decisión.</p>
      <ul v-else class="inicio__lista">
        <li v-for="p in pendientes" :key="p.a">
          <RouterLink :to="p.a" class="inicio__fila">
            <component :is="p.icono" class="inicio__icono" aria-hidden="true" />
            <span class="inicio__texto">
              <strong class="inicio__cantidad">{{ p.cantidad }}</strong>
              {{ p.texto(p.cantidad) }}
            </span>
          </RouterLink>
        </li>
      </ul>
    </section>

    <section class="inicio__bloque" aria-labelledby="titulo-accesos">
      <h2 id="titulo-accesos" class="inicio__subtitulo">Lo más usado</h2>
      <ul class="inicio__lista">
        <li v-for="acceso in accesos" :key="acceso.a">
          <RouterLink :to="acceso.a" class="inicio__fila">
            <component :is="acceso.icono" class="inicio__icono" aria-hidden="true" />
            <span class="inicio__texto">
              <span class="inicio__etiqueta">{{ acceso.etiqueta }}</span>
              <span class="inicio__detalle">{{ acceso.detalle }}</span>
            </span>
          </RouterLink>
        </li>
      </ul>
    </section>
  </section>
</template>

<style scoped>
.inicio__bloque + .inicio__bloque {
  margin-top: var(--espacio-3xl);
}

.inicio__subtitulo {
  font-size: var(--texto-md);
  margin-bottom: var(--espacio-md);
}

.inicio__al-dia {
  margin: 0;
  color: var(--color-tinta-suave);
}

/* Filas con línea, no tarjetas (sección 15.4): una lista que se recorre
   con el pulgar en el teléfono y con la vista en escritorio. */
.inicio__lista {
  list-style: none;
  margin: 0;
  padding: 0;
  max-width: 40rem;
  background: var(--color-papel);
  border: 1px solid var(--color-linea);
  border-radius: var(--radio-lg);
}

.inicio__lista li + li {
  border-top: 1px solid var(--color-linea);
}

.inicio__fila {
  display: flex;
  align-items: center;
  gap: var(--espacio-md);
  min-height: 3.5rem;
  padding: var(--espacio-md) var(--espacio-lg);
  color: var(--color-tinta);
  text-decoration: none;
}

.inicio__fila:hover {
  background: var(--color-fondo);
}

.inicio__lista li:first-child .inicio__fila {
  border-radius: var(--radio-lg) var(--radio-lg) 0 0;
}

.inicio__lista li:last-child .inicio__fila {
  border-radius: 0 0 var(--radio-lg) var(--radio-lg);
}

.inicio__icono {
  flex: none;
  width: 1.25rem;
  height: 1.25rem;
  color: var(--color-accion);
}

.inicio__texto {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.inicio__cantidad {
  font-family: var(--fuente-titulo);
  font-size: var(--texto-lg);
  line-height: 1;
  color: var(--color-tinta);
}

.inicio__etiqueta {
  font-weight: 600;
}

.inicio__detalle {
  font-size: var(--texto-sm);
  color: var(--color-tinta-suave);
}

</style>
