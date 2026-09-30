<script setup lang="ts">
import { Copy, KeyRound, Pencil, Power, RefreshCw } from "lucide-vue-next";
import { computed, onMounted, reactive, ref } from "vue";

import { useAuthStore } from "@/features/auth/stores/authStore";
import {
  AppButton,
  AppModal,
  CargandoBloque,
  DataTable,
  ErrorBanner,
  FormField,
  FormSelect,
  PageHeader,
  TagPill,
} from "@/shared/components";
import type { ColumnaTabla } from "@/shared/components/DataTable.vue";
import { avisar } from "@/shared/composables/useAvisos";
import { confirmar } from "@/shared/composables/useConfirmar";
import { generarContrasenaTemporal } from "@/shared/contrasenaTemporal";
import { type Area, usePermisos } from "@/shared/permisos";
import type { Role, Usuario } from "@/shared/types/models";

import { crearUsuario, listarRoles, restablecerContrasena, usuariosApi } from "../api/usuariosApi";

// Las cuentas de familia nacen junto con su perfil de encargado y el
// vínculo con el estudiante (pantalla Encargados); crearlas acá dejaría
// una cuenta suelta que no ve a nadie.
const ROL_FAMILIA = "Padre de familia";

type Variante = "taller" | "aviso" | "hoy" | "alerta" | "neutro";

const auth = useAuthStore();
const permisos = usePermisos();
const puedeEditar = computed(() => permisos.puedeEditar("usuarios_roles"));

const usuarios = ref<Usuario[]>([]);
const roles = ref<Role[]>([]);
const cargando = ref(true);
const error = ref("");

const filtroRol = ref("");
const filtroEstado = ref("activos");

async function cargar(): Promise<void> {
  cargando.value = true;
  error.value = "";
  try {
    const [usuariosResp, rolesResp] = await Promise.all([usuariosApi.listar(), listarRoles()]);
    usuarios.value = usuariosResp.results;
    roles.value = rolesResp;
  } catch {
    error.value = "No se pudo cargar la lista de usuarios. Probá de nuevo.";
  } finally {
    cargando.value = false;
  }
}

const usuariosFiltrados = computed(() =>
  usuarios.value.filter((u) => {
    if (filtroRol.value && u.role !== filtroRol.value) return false;
    if (filtroEstado.value === "activos") return u.is_active !== false;
    if (filtroEstado.value === "inactivos") return u.is_active === false;
    return true;
  }),
);

const opcionesFiltroRol = computed(() => [
  { valor: "", etiqueta: "Todos los roles" },
  ...roles.value.map((r) => ({ valor: r.public_id, etiqueta: r.name })),
]);
const opcionesEstado = [
  { valor: "activos", etiqueta: "Activas" },
  { valor: "inactivos", etiqueta: "Desactivadas" },
  { valor: "todos", etiqueta: "Todas" },
];
const opcionesRolFormulario = computed(() =>
  roles.value.filter((r) => r.name !== ROL_FAMILIA).map((r) => ({ valor: r.public_id, etiqueta: r.name })),
);
const opcionesRolVisto = computed(() => roles.value.map((r) => ({ valor: r.public_id, etiqueta: r.name })));

function nombreCompleto(u: Usuario): string {
  return [u.first_name, u.last_name].filter(Boolean).join(" ") || u.username;
}

const formatoFecha = new Intl.DateTimeFormat("es-GT", { dateStyle: "medium", timeStyle: "short" });
const formatoHora = new Intl.DateTimeFormat("es-GT", { timeStyle: "short" });

function ultimoIngreso(u: Usuario): string {
  return u.last_login ? formatoFecha.format(new Date(u.last_login)) : "Nunca";
}

function estado(u: Usuario): { texto: string; variante: Variante } {
  if (u.is_active === false) return { texto: "Desactivada", variante: "neutro" };
  if (u.locked_until && new Date(u.locked_until) > new Date()) {
    return { texto: `Bloqueada hasta las ${formatoHora.format(new Date(u.locked_until))}`, variante: "alerta" };
  }
  if (u.must_change_password) return { texto: "Sin primer ingreso", variante: "aviso" };
  return { texto: "Activa", variante: "taller" };
}

const columnas: ColumnaTabla<Usuario>[] = [
  { clave: "nombre", etiqueta: "Nombre", texto: nombreCompleto },
  { clave: "username", etiqueta: "Usuario" },
  { clave: "role_name", etiqueta: "Rol" },
  { clave: "estado", etiqueta: "Estado", texto: (u) => estado(u).texto },
  { clave: "last_login", etiqueta: "Último ingreso", texto: ultimoIngreso },
];

function esYo(u: Usuario): boolean {
  return u.public_id === auth.usuario?.public_id;
}

function mensajeDeError(e: unknown, porDefecto: string): string {
  const datos = (e as { response?: { data?: Record<string, unknown> } }).response?.data;
  if (datos && typeof datos === "object") {
    const primero = Object.values(datos)[0];
    if (Array.isArray(primero) && typeof primero[0] === "string") return primero[0];
    if (typeof primero === "string") return primero;
  }
  return porDefecto;
}

// ---- Diálogos ----
const modal = ref<"crear" | "editar" | "restablecer" | null>(null);
const guardando = ref(false);
const errorModal = ref("");
const credenciales = ref<{ usuario: string; contrasena: string } | null>(null);
const seleccionado = ref<Usuario | null>(null);
const formulario = reactive({
  username: "",
  first_name: "",
  last_name: "",
  email: "",
  role: "",
  contrasena: "",
});

function abrirCrear(): void {
  Object.assign(formulario, {
    username: "",
    first_name: "",
    last_name: "",
    email: "",
    role: opcionesRolFormulario.value[0]?.valor ?? "",
    contrasena: generarContrasenaTemporal(),
  });
  credenciales.value = null;
  errorModal.value = "";
  modal.value = "crear";
}

async function guardarNuevo(): Promise<void> {
  guardando.value = true;
  errorModal.value = "";
  try {
    const creado = await crearUsuario({
      username: formulario.username.trim(),
      first_name: formulario.first_name.trim(),
      last_name: formulario.last_name.trim(),
      email: formulario.email.trim(),
      role: formulario.role,
      contrasena_temporal: formulario.contrasena,
    });
    credenciales.value = { usuario: creado.username, contrasena: formulario.contrasena };
    await cargar();
  } catch (e) {
    errorModal.value = mensajeDeError(e, "No se pudo crear el usuario. Revisá los datos.");
  } finally {
    guardando.value = false;
  }
}

function abrirEditar(u: Usuario): void {
  seleccionado.value = u;
  Object.assign(formulario, {
    first_name: u.first_name ?? "",
    last_name: u.last_name ?? "",
    email: u.email ?? "",
    role: u.role,
  });
  errorModal.value = "";
  modal.value = "editar";
}

async function guardarEdicion(): Promise<void> {
  if (!seleccionado.value) return;
  guardando.value = true;
  errorModal.value = "";
  try {
    const cambios: Partial<Usuario> = {
      first_name: formulario.first_name.trim(),
      last_name: formulario.last_name.trim(),
      email: formulario.email.trim(),
    };
    if (!esYo(seleccionado.value)) cambios.role = formulario.role;
    await usuariosApi.actualizar(seleccionado.value.public_id, cambios);
    modal.value = null;
    avisar("Cambios guardados.");
    await cargar();
  } catch (e) {
    errorModal.value = mensajeDeError(e, "No se pudieron guardar los cambios.");
  } finally {
    guardando.value = false;
  }
}

function abrirRestablecer(u: Usuario): void {
  seleccionado.value = u;
  formulario.contrasena = generarContrasenaTemporal();
  credenciales.value = null;
  errorModal.value = "";
  modal.value = "restablecer";
}

async function guardarRestablecer(): Promise<void> {
  if (!seleccionado.value) return;
  guardando.value = true;
  errorModal.value = "";
  try {
    await restablecerContrasena(seleccionado.value.public_id, formulario.contrasena);
    credenciales.value = { usuario: seleccionado.value.username, contrasena: formulario.contrasena };
    await cargar();
  } catch (e) {
    errorModal.value = mensajeDeError(e, "No se pudo restablecer la contraseña.");
  } finally {
    guardando.value = false;
  }
}

async function cambiarActiva(u: Usuario): Promise<void> {
  const activar = u.is_active === false;
  if (!activar) {
    const confirmado = await confirmar({
      titulo: `¿Desactivar la cuenta de ${nombreCompleto(u)}?`,
      mensaje:
        "No va a poder entrar al sistema. Todo lo que registró se conserva, y la cuenta se puede volver a activar.",
      etiquetaConfirmar: "Desactivar",
      peligro: true,
    });
    if (!confirmado) return;
  }
  try {
    await usuariosApi.actualizar(u.public_id, { is_active: activar });
    avisar(activar ? "Cuenta activada." : "Cuenta desactivada.");
    await cargar();
  } catch (e) {
    avisar(mensajeDeError(e, "No se pudo cambiar el estado de la cuenta."), "error");
  }
}

async function copiarCredenciales(): Promise<void> {
  if (!credenciales.value) return;
  try {
    await navigator.clipboard.writeText(
      `Usuario: ${credenciales.value.usuario}\nContraseña temporal: ${credenciales.value.contrasena}`,
    );
    avisar("Datos copiados.");
  } catch {
    avisar("No se pudo copiar. Anotalos a mano.", "error");
  }
}

// ---- Roles y permisos (solo lectura) ----
const AREAS: { area: Area; etiqueta: string }[] = [
  { area: "usuarios_roles", etiqueta: "Usuarios y roles" },
  { area: "datos_maestros", etiqueta: "Datos maestros" },
  { area: "estudiantes_encargados", etiqueta: "Estudiantes y encargados" },
  { area: "datos_sensibles", etiqueta: "Datos sensibles" },
  { area: "horarios_calendario", etiqueta: "Horarios y calendario" },
  { area: "asistencia", etiqueta: "Asistencia" },
  { area: "notas", etiqueta: "Notas" },
  { area: "modificacion_notas", etiqueta: "Autorizar cambios de nota" },
  { area: "pagos_solvencia", etiqueta: "Pagos y solvencia" },
  { area: "documentos", etiqueta: "Documentos" },
  { area: "avisos", etiqueta: "Avisos" },
  { area: "reportes_conducta", etiqueta: "Reportes de conducta" },
  { area: "buzon", etiqueta: "Buzón" },
  { area: "reportes_institucionales", etiqueta: "Reportes institucionales" },
  { area: "bitacora_registro_acceso", etiqueta: "Bitácora" },
];
const NIVELES: Record<string, { texto: string; variante: Variante }> = {
  editar: { texto: "Edita", variante: "taller" },
  ver: { texto: "Solo ve", variante: "hoy" },
  sin_acceso: { texto: "Sin acceso", variante: "neutro" },
};
const rolVisto = ref("");
const permisosDelRol = computed(() => {
  const rol = roles.value.find((r) => r.public_id === rolVisto.value);
  const permisosRol = (rol?.permissions ?? {}) as Record<string, string>;
  return AREAS.map(({ area, etiqueta }) => ({ etiqueta, ...(NIVELES[permisosRol[area]] ?? NIVELES.sin_acceso) }));
});

onMounted(async () => {
  await cargar();
  rolVisto.value = roles.value[0]?.public_id ?? "";
});
</script>

<template>
  <section class="usuarios-page">
    <PageHeader titulo="Usuarios" descripcion="Cuentas del personal y de las familias, y lo que puede hacer cada rol.">
      <template #acciones>
        <AppButton v-if="puedeEditar" :deshabilitado="cargando" @click="abrirCrear">Crear usuario</AppButton>
      </template>
    </PageHeader>

    <ErrorBanner v-if="error" :mensaje="error" etiqueta-accion="Reintentar" @accion="cargar" />
    <CargandoBloque v-else-if="cargando" />

    <template v-else>
      <div class="usuarios-page__filtros">
        <FormSelect id="filtro-rol" etiqueta="Rol" :opciones="opcionesFiltroRol" v-model="filtroRol" />
        <FormSelect id="filtro-estado" etiqueta="Cuentas" :opciones="opcionesEstado" v-model="filtroEstado" />
      </div>

      <DataTable
        :columnas="columnas"
        :filas="usuariosFiltrados"
        buscable
        placeholder-busqueda="Buscar por nombre o usuario"
        descripcion="Usuarios del sistema"
      >
        <template #celda-nombre="{ fila }">
          {{ nombreCompleto(fila) }}
          <TagPill v-if="esYo(fila)" variante="hoy" class="usuarios-page__yo">Vos</TagPill>
        </template>
        <template #celda-estado="{ fila }">
          <TagPill :variante="estado(fila).variante">{{ estado(fila).texto }}</TagPill>
        </template>
        <template #celda-last_login="{ fila }">{{ ultimoIngreso(fila) }}</template>
        <template v-if="puedeEditar" #acciones="{ fila }">
          <AppButton variante="discreto" compacto @click="abrirEditar(fila)">
            <Pencil aria-hidden="true" />
            Editar
          </AppButton>
          <AppButton
            variante="discreto"
            compacto
            :aria-label="`Restablecer la contraseña de ${fila.username}`"
            @click="abrirRestablecer(fila)"
          >
            <KeyRound aria-hidden="true" />
            Restablecer
          </AppButton>
          <AppButton v-if="!esYo(fila)" variante="discreto" compacto @click="cambiarActiva(fila)">
            <Power aria-hidden="true" />
            {{ fila.is_active === false ? "Activar" : "Desactivar" }}
          </AppButton>
        </template>
      </DataTable>

      <details class="usuarios-page__permisos">
        <summary>Qué puede hacer cada rol</summary>
        <p class="usuarios-page__nota">
          Los permisos siguen la matriz aprobada por dirección. Se consultan acá, pero no se editan desde el sistema.
        </p>
        <FormSelect id="rol-visto" etiqueta="Rol" :opciones="opcionesRolVisto" v-model="rolVisto" />
        <ul class="usuarios-page__lista-permisos">
          <li v-for="p in permisosDelRol" :key="p.etiqueta">
            <span>{{ p.etiqueta }}</span>
            <TagPill :variante="p.variante">{{ p.texto }}</TagPill>
          </li>
        </ul>
      </details>
    </template>

    <AppModal v-if="modal === 'crear'" titulo="Crear usuario" @cerrar="modal = null">
      <template v-if="credenciales">
        <p class="usuarios-page__exito">La cuenta quedó creada. Entregale estos datos a la persona:</p>
        <dl class="usuarios-page__credenciales">
          <dt>Usuario</dt>
          <dd>{{ credenciales.usuario }}</dd>
          <dt>Contraseña temporal</dt>
          <dd>{{ credenciales.contrasena }}</dd>
        </dl>
        <p class="usuarios-page__nota">En su primer ingreso el sistema le va a pedir que la cambie.</p>
        <div class="usuarios-page__acciones-modal">
          <AppButton variante="secundario" @click="copiarCredenciales">
            <Copy aria-hidden="true" />
            Copiar datos
          </AppButton>
          <AppButton @click="modal = null">Listo</AppButton>
        </div>
      </template>
      <form v-else class="usuarios-page__formulario" @submit.prevent="guardarNuevo">
        <ErrorBanner v-if="errorModal" :mensaje="errorModal" />
        <FormField
          id="nuevo-usuario"
          etiqueta="Nombre de usuario"
          v-model="formulario.username"
          pista="Con el que va a entrar. Por ejemplo, maria.perez"
          autocapitalize="none"
          spellcheck="false"
          required
        />
        <div class="usuarios-page__dos-columnas">
          <FormField id="nuevo-nombres" etiqueta="Nombres" v-model="formulario.first_name" required />
          <FormField id="nuevo-apellidos" etiqueta="Apellidos" v-model="formulario.last_name" required />
        </div>
        <FormField id="nuevo-correo" etiqueta="Correo (opcional)" tipo="email" v-model="formulario.email" />
        <div>
          <FormSelect id="nuevo-rol" etiqueta="Rol" :opciones="opcionesRolFormulario" v-model="formulario.role" />
          <p class="usuarios-page__nota usuarios-page__nota--debajo">
            Las cuentas de familias se crean desde Encargados, junto con su vínculo al estudiante.
          </p>
        </div>
        <div class="usuarios-page__contrasena">
          <FormField id="nuevo-contrasena" etiqueta="Contraseña temporal" v-model="formulario.contrasena" required />
          <AppButton variante="secundario" @click="formulario.contrasena = generarContrasenaTemporal()">
            <RefreshCw aria-hidden="true" />
            Otra
          </AppButton>
        </div>
        <AppButton tipo="submit" bloque :deshabilitado="guardando">
          {{ guardando ? "Creando…" : "Crear usuario" }}
        </AppButton>
      </form>
    </AppModal>

    <AppModal
      v-if="modal === 'editar' && seleccionado"
      :titulo="`Editar ${seleccionado.username}`"
      @cerrar="modal = null"
    >
      <form class="usuarios-page__formulario" @submit.prevent="guardarEdicion">
        <ErrorBanner v-if="errorModal" :mensaje="errorModal" />
        <div class="usuarios-page__dos-columnas">
          <FormField id="editar-nombres" etiqueta="Nombres" v-model="formulario.first_name" />
          <FormField id="editar-apellidos" etiqueta="Apellidos" v-model="formulario.last_name" />
        </div>
        <FormField id="editar-correo" etiqueta="Correo (opcional)" tipo="email" v-model="formulario.email" />
        <template v-if="seleccionado.role_name !== ROL_FAMILIA">
          <p v-if="esYo(seleccionado)" class="usuarios-page__nota">
            No podés cambiar tu propio rol: pedíselo a otra persona con este permiso.
          </p>
          <FormSelect v-else id="editar-rol" etiqueta="Rol" :opciones="opcionesRolFormulario" v-model="formulario.role" />
        </template>
        <AppButton tipo="submit" bloque :deshabilitado="guardando">
          {{ guardando ? "Guardando…" : "Guardar cambios" }}
        </AppButton>
      </form>
    </AppModal>

    <AppModal
      v-if="modal === 'restablecer' && seleccionado"
      :titulo="`Restablecer contraseña de ${seleccionado.username}`"
      @cerrar="modal = null"
    >
      <template v-if="credenciales">
        <p class="usuarios-page__exito">Listo. Entregale la contraseña temporal nueva:</p>
        <dl class="usuarios-page__credenciales">
          <dt>Usuario</dt>
          <dd>{{ credenciales.usuario }}</dd>
          <dt>Contraseña temporal</dt>
          <dd>{{ credenciales.contrasena }}</dd>
        </dl>
        <div class="usuarios-page__acciones-modal">
          <AppButton variante="secundario" @click="copiarCredenciales">
            <Copy aria-hidden="true" />
            Copiar datos
          </AppButton>
          <AppButton @click="modal = null">Listo</AppButton>
        </div>
      </template>
      <form v-else class="usuarios-page__formulario" @submit.prevent="guardarRestablecer">
        <ErrorBanner v-if="errorModal" :mensaje="errorModal" />
        <p class="usuarios-page__nota">
          La contraseña actual deja de servir y, si la cuenta estaba bloqueada, se desbloquea. En el próximo ingreso
          le va a pedir una nueva.
        </p>
        <div class="usuarios-page__contrasena">
          <FormField
            id="restablecer-contrasena"
            etiqueta="Contraseña temporal"
            v-model="formulario.contrasena"
            required
          />
          <AppButton variante="secundario" @click="formulario.contrasena = generarContrasenaTemporal()">
            <RefreshCw aria-hidden="true" />
            Otra
          </AppButton>
        </div>
        <AppButton tipo="submit" bloque :deshabilitado="guardando">
          {{ guardando ? "Restableciendo…" : "Restablecer contraseña" }}
        </AppButton>
      </form>
    </AppModal>
  </section>
</template>

<style scoped>
.usuarios-page__filtros {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--espacio-md);
  margin-bottom: var(--espacio-lg);
}

.usuarios-page__yo {
  margin-left: var(--espacio-xs);
  vertical-align: middle;
}

.usuarios-page__formulario {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-lg);
}

.usuarios-page__dos-columnas {
  display: grid;
  gap: var(--espacio-lg);
}

.usuarios-page__contrasena {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: end;
  gap: var(--espacio-sm);
}

.usuarios-page__nota {
  margin: 0;
  font-size: var(--texto-sm);
  color: var(--color-tinta-suave);
}

.usuarios-page__nota--debajo {
  margin-top: var(--espacio-xs);
}

.usuarios-page__exito {
  margin: 0;
  font-weight: 600;
}

.usuarios-page__credenciales {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: var(--espacio-xs) var(--espacio-lg);
  margin: 0;
  padding: var(--espacio-lg);
  background: var(--color-fondo);
  border-radius: var(--radio-md);
}

.usuarios-page__credenciales dt {
  color: var(--color-tinta-suave);
  font-size: var(--texto-sm);
}

.usuarios-page__credenciales dd {
  margin: 0;
  font-family: ui-monospace, "Cascadia Mono", Consolas, monospace;
  font-weight: 600;
  overflow-wrap: anywhere;
}

.usuarios-page__acciones-modal {
  display: flex;
  flex-direction: column-reverse;
  gap: var(--espacio-sm);
}

.usuarios-page__permisos {
  margin-top: var(--espacio-3xl);
  max-width: 40rem;
  padding: var(--espacio-sm) var(--espacio-lg) var(--espacio-lg);
  background: var(--color-papel);
  border: 1px solid var(--color-linea);
  border-radius: var(--radio-lg);
}

.usuarios-page__permisos summary {
  display: flex;
  align-items: center;
  min-height: var(--area-tactil-minima);
  font-family: var(--fuente-titulo);
  font-weight: 700;
  cursor: pointer;
}

.usuarios-page__permisos:not([open]) {
  padding-bottom: var(--espacio-sm);
}

.usuarios-page__permisos > * + * {
  margin-top: var(--espacio-lg);
}

.usuarios-page__lista-permisos {
  list-style: none;
  margin: 0;
  padding: 0;
}

.usuarios-page__lista-permisos li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--espacio-md);
  min-height: 2.75rem;
  border-bottom: 1px solid var(--color-linea);
  font-size: var(--texto-sm);
}

.usuarios-page__lista-permisos li:last-child {
  border-bottom: none;
}

@media (min-width: 40rem) {
  .usuarios-page__filtros {
    grid-template-columns: repeat(2, minmax(0, 16rem));
  }

  .usuarios-page__dos-columnas {
    grid-template-columns: 1fr 1fr;
  }

  .usuarios-page__acciones-modal {
    flex-direction: row;
    justify-content: flex-end;
  }
}
</style>
