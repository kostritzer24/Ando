<script setup lang="ts">
import { LogOut, Menu, UserRound, X } from "lucide-vue-next";
import { computed, nextTick, onBeforeUnmount, ref, watch, type Component } from "vue";
import { useRoute, useRouter } from "vue-router";

import { useAuthStore } from "@/features/auth/stores/authStore";
import { type Area, type Nivel, usePermisos } from "@/shared/permisos";

export interface ItemNavegacion {
  a: string;
  etiqueta: string;
  icono: Component;
  /** Área de docs/permisos-roles.md que la pantalla consulta: la opción
   * solo aparece si el rol tiene al menos `nivel` ("ver" por omisión). */
  area?: Area;
  nivel?: Nivel;
  /** Condición extra que no es de permisos sino de negocio (la plantilla
   * de talleres es solo para Tallerista). */
  visible?: boolean;
  /** Solo se marca activo en esa ruta exacta (el "Inicio" del portal,
   * que es prefijo de todas las demás). */
  exacto?: boolean;
}

export interface GrupoNavegacion {
  /** Sin título, el grupo va primero y sin encabezado (Inicio). */
  titulo?: string;
  items: ItemNavegacion[];
}

const props = defineProps<{
  portal: string;
  navegacion: GrupoNavegacion[];
  /** Pantalla "Mi cuenta" del portal (datos propios y cambio de contraseña). */
  rutaCuenta: string;
}>();

const auth = useAuthStore();
const { nivel } = usePermisos();

function alcanza(item: ItemNavegacion): boolean {
  if (item.visible === false) return false;
  if (!item.area) return true;
  const tiene = nivel(item.area);
  return item.nivel === "editar" ? tiene === "editar" : tiene !== "sin_acceso";
}

// Los grupos que se quedan sin opciones para este rol no se muestran.
const gruposVisibles = computed(() =>
  props.navegacion
    .map((grupo) => ({ ...grupo, items: grupo.items.filter(alcanza) }))
    .filter((grupo) => grupo.items.length > 0),
);
const route = useRoute();
const router = useRouter();

const menuAbierto = ref(false);
const botonMenu = ref<HTMLButtonElement | null>(null);
const panel = ref<HTMLElement | null>(null);

const nombreUsuario = computed(
  () =>
    [auth.usuario?.first_name, auth.usuario?.last_name].filter(Boolean).join(" ") ||
    auth.usuario?.username ||
    "",
);
const iniciales = computed(() =>
  nombreUsuario.value
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((parte) => parte[0]?.toUpperCase())
    .join(""),
);

function estaActivo(item: ItemNavegacion): boolean {
  if (item.exacto) return route.path === item.a;
  return route.path === item.a || route.path.startsWith(`${item.a}/`);
}

async function abrirMenu(): Promise<void> {
  menuAbierto.value = true;
  document.body.classList.add("sin-desplazamiento");
  await nextTick();
  panel.value?.querySelector<HTMLElement>("a")?.focus();
}

function cerrarMenu(devolverFoco = true): void {
  if (!menuAbierto.value) return;
  menuAbierto.value = false;
  document.body.classList.remove("sin-desplazamiento");
  if (devolverFoco) botonMenu.value?.focus();
}

function alPresionarTecla(evento: KeyboardEvent): void {
  if (evento.key === "Escape") cerrarMenu();
}

// Elegir una opción del menú en el teléfono lleva a otra pantalla: el
// panel se cierra solo, sin robar el foco al contenido nuevo.
watch(
  () => route.fullPath,
  () => cerrarMenu(false),
);

onBeforeUnmount(() => document.body.classList.remove("sin-desplazamiento"));

async function salir(): Promise<void> {
  await auth.salir();
  router.push({ name: "ingresar" });
}
</script>

<template>
  <div class="admin-shell" @keydown="alPresionarTecla">
    <a href="#contenido" class="admin-shell__saltar">Saltar al contenido</a>

    <header class="admin-shell__barra">
      <button
        ref="botonMenu"
        type="button"
        class="admin-shell__boton-icono admin-shell__boton-menu"
        aria-controls="menu-principal"
        :aria-expanded="menuAbierto"
        @click="abrirMenu"
      >
        <Menu aria-hidden="true" />
        <span class="solo-lector">Abrir menú</span>
      </button>

      <RouterLink :to="navegacion[0]?.items[0]?.a ?? '/'" class="admin-shell__marca admin-shell__marca--barra">
        <img src="/marca.png" alt="" width="28" height="28" />
        <span>El Patojismo</span>
      </RouterLink>

      <div class="admin-shell__usuario">
        <RouterLink :to="rutaCuenta" class="admin-shell__cuenta" title="Mi cuenta">
          <span class="admin-shell__avatar" aria-hidden="true">{{ iniciales }}</span>
          <span class="admin-shell__usuario-textos">
            <span class="admin-shell__usuario-nombre">{{ nombreUsuario }}</span>
            <span class="admin-shell__usuario-rol">{{ auth.usuario?.role_name }}</span>
          </span>
          <span class="solo-lector">Mi cuenta</span>
        </RouterLink>
        <button type="button" class="admin-shell__salir" @click="salir">
          <LogOut aria-hidden="true" />
          Cerrar sesión
        </button>
      </div>
    </header>

    <div v-if="menuAbierto" class="admin-shell__velo" aria-hidden="true" @click="cerrarMenu()" />

    <aside
      id="menu-principal"
      ref="panel"
      class="admin-shell__panel"
      :class="{ 'admin-shell__panel--abierto': menuAbierto }"
    >
      <div class="admin-shell__panel-cabecera">
        <RouterLink :to="navegacion[0]?.items[0]?.a ?? '/'" class="admin-shell__marca">
          <img src="/marca.png" alt="" width="32" height="32" />
          <span class="admin-shell__marca-textos">
            <span>El Patojismo</span>
            <span class="admin-shell__portal">{{ portal }}</span>
          </span>
        </RouterLink>
        <button type="button" class="admin-shell__boton-icono admin-shell__cerrar-menu" @click="cerrarMenu()">
          <X aria-hidden="true" />
          <span class="solo-lector">Cerrar menú</span>
        </button>
      </div>

      <nav class="admin-shell__nav" aria-label="Navegación principal">
        <div v-for="(grupo, indice) in gruposVisibles" :key="grupo.titulo ?? indice" class="admin-shell__grupo">
          <p v-if="grupo.titulo" class="admin-shell__grupo-titulo">{{ grupo.titulo }}</p>
          <RouterLink
            v-for="item in grupo.items"
            :key="item.a"
            :to="item.a"
            class="admin-shell__enlace"
            :class="{ 'admin-shell__enlace--activo': estaActivo(item) }"
            :aria-current="estaActivo(item) ? 'page' : undefined"
          >
            <component :is="item.icono" class="admin-shell__enlace-icono" aria-hidden="true" />
            {{ item.etiqueta }}
          </RouterLink>
        </div>
      </nav>

      <div class="admin-shell__panel-pie">
        <div class="admin-shell__usuario-pie">
          <span class="admin-shell__avatar" aria-hidden="true">{{ iniciales }}</span>
          <span class="admin-shell__usuario-textos">
            <span class="admin-shell__usuario-nombre">{{ nombreUsuario }}</span>
            <span class="admin-shell__usuario-rol">{{ auth.usuario?.role_name }}</span>
          </span>
        </div>
        <div class="admin-shell__acciones-pie">
          <RouterLink :to="rutaCuenta" class="admin-shell__salir admin-shell__salir--pie">
            <UserRound aria-hidden="true" />
            Mi cuenta
          </RouterLink>
          <button type="button" class="admin-shell__salir admin-shell__salir--pie" @click="salir">
            <LogOut aria-hidden="true" />
            Cerrar sesión
          </button>
        </div>
      </div>
    </aside>

    <main id="contenido" class="admin-shell__main" tabindex="-1">
      <slot />
    </main>
  </div>
</template>

<style scoped>
/* Mobile-first. En el teléfono: barra superior fija con el botón de menú
   y un panel lateral que se abre encima del contenido. Desde 64rem: el
   panel es una barra lateral fija y la barra superior solo lleva al
   usuario. */
.admin-shell {
  min-height: 100vh;
  min-height: 100dvh;
}

.admin-shell__saltar {
  position: absolute;
  left: var(--espacio-sm);
  top: -4rem;
  z-index: calc(var(--capa-modal) + 1);
  padding: var(--espacio-sm) var(--espacio-md);
  background: var(--color-accion);
  color: var(--color-papel);
  border-radius: var(--radio-md);
  font-weight: 600;
}

.admin-shell__saltar:focus {
  top: var(--espacio-sm);
}

/* ---- Barra superior ---- */
.admin-shell__barra {
  position: sticky;
  top: 0;
  z-index: var(--capa-barra);
  display: flex;
  align-items: center;
  gap: var(--espacio-xs);
  height: var(--alto-barra);
  padding: 0 var(--espacio-sm);
  padding-top: env(safe-area-inset-top, 0px);
  background: var(--color-papel);
  border-bottom: 1px solid var(--color-linea);
}

.admin-shell__boton-icono {
  flex: none;
  display: grid;
  place-items: center;
  width: var(--area-tactil-minima);
  height: var(--area-tactil-minima);
  background: none;
  border: none;
  border-radius: var(--radio-md);
  color: var(--color-tinta);
  cursor: pointer;
}

.admin-shell__boton-icono:hover {
  background: var(--color-hover);
}

.admin-shell__boton-icono svg {
  width: 1.5rem;
  height: 1.5rem;
}

.admin-shell__marca {
  display: flex;
  align-items: center;
  gap: var(--espacio-sm);
  min-width: 0;
  font-family: var(--fuente-titulo);
  font-weight: 800;
  font-size: var(--texto-md);
  color: var(--color-tinta);
  text-decoration: none;
}

.admin-shell__marca img {
  flex: none;
}

.admin-shell__marca-textos {
  display: flex;
  flex-direction: column;
  line-height: 1.15;
}

.admin-shell__portal {
  font-family: var(--fuente-cuerpo);
  font-weight: 500;
  font-size: var(--texto-xs);
  color: var(--color-tinta-suave);
}

.admin-shell__usuario {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: var(--espacio-md);
  padding-right: var(--espacio-xs);
}

.admin-shell__cuenta {
  display: flex;
  align-items: center;
  gap: var(--espacio-md);
  min-width: 0;
  min-height: var(--area-tactil-minima);
  padding: 0 var(--espacio-xs);
  border-radius: var(--radio-md);
  color: inherit;
  text-decoration: none;
}

.admin-shell__cuenta:hover {
  background: var(--color-hover);
}

.admin-shell__avatar {
  flex: none;
  display: grid;
  place-items: center;
  width: 2.25rem;
  height: 2.25rem;
  border-radius: 50%;
  background: var(--color-accion-suave);
  color: var(--color-accion);
  font-size: var(--texto-sm);
  font-weight: 700;
}

.admin-shell__usuario-textos {
  display: none;
  flex-direction: column;
  min-width: 0;
  line-height: 1.25;
}

.admin-shell__usuario-nombre {
  font-size: var(--texto-sm);
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.admin-shell__usuario-rol {
  font-size: var(--texto-xs);
  color: var(--color-tinta-suave);
}

.admin-shell__salir {
  display: none;
  align-items: center;
  gap: var(--espacio-xs);
  min-height: 2.5rem;
  padding: 0 var(--espacio-md);
  background: none;
  border: 1px solid var(--color-linea-fuerte);
  border-radius: var(--radio-md);
  font-size: var(--texto-sm);
  font-weight: 600;
  color: var(--color-tinta);
  cursor: pointer;
}

.admin-shell__salir:hover {
  background: var(--color-hover);
}

.admin-shell__salir svg {
  width: 1.05rem;
  height: 1.05rem;
}

/* ---- Panel de navegación ---- */
.admin-shell__velo {
  position: fixed;
  inset: 0;
  z-index: var(--capa-menu);
  background: rgb(20 24 28 / 40%);
}

.admin-shell__panel {
  position: fixed;
  inset: 0 auto 0 0;
  z-index: calc(var(--capa-menu) + 1);
  display: flex;
  flex-direction: column;
  width: min(var(--ancho-menu), 85vw);
  background: var(--color-papel);
  box-shadow: var(--sombra-flotante);
  transform: translateX(-100%);
  visibility: hidden;
  transition:
    transform 200ms ease-out,
    visibility 0s linear 200ms;
}

.admin-shell__panel--abierto {
  transform: none;
  visibility: visible;
  transition: transform 200ms ease-out;
}

.admin-shell__panel-cabecera {
  flex: none;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--espacio-sm);
  min-height: var(--alto-barra);
  padding: var(--espacio-sm) var(--espacio-xs) var(--espacio-sm) var(--espacio-lg);
  border-bottom: 1px solid var(--color-linea);
}

.admin-shell__nav {
  flex: 1;
  overflow-y: auto;
  overscroll-behavior: contain;
  padding: var(--espacio-sm) var(--espacio-sm) var(--espacio-lg);
}

.admin-shell__grupo + .admin-shell__grupo {
  margin-top: var(--espacio-md);
}

.admin-shell__grupo-titulo {
  margin: 0;
  padding: var(--espacio-sm) var(--espacio-md) var(--espacio-xs);
  font-size: var(--texto-xs);
  font-weight: 600;
  color: var(--color-tinta-suave);
}

.admin-shell__enlace {
  display: flex;
  align-items: center;
  gap: var(--espacio-md);
  min-height: var(--area-tactil-minima);
  padding: 0 var(--espacio-md);
  border-radius: var(--radio-md);
  font-size: var(--texto-sm);
  font-weight: 500;
  color: var(--color-tinta);
  text-decoration: none;
}

.admin-shell__enlace:hover {
  background: var(--color-hover);
}

.admin-shell__enlace-icono {
  flex: none;
  width: 1.2rem;
  height: 1.2rem;
  color: var(--color-tinta-suave);
}

.admin-shell__enlace--activo {
  background: var(--color-accion-suave);
  color: var(--color-accion);
  font-weight: 600;
}

.admin-shell__enlace--activo:hover {
  background: var(--color-accion-suave);
}

.admin-shell__enlace--activo .admin-shell__enlace-icono {
  color: var(--color-accion);
}

.admin-shell__enlace:focus-visible {
  outline-offset: -2px;
}

.admin-shell__panel-pie {
  flex: none;
  display: flex;
  flex-direction: column;
  gap: var(--espacio-md);
  padding: var(--espacio-lg);
  padding-bottom: calc(var(--espacio-lg) + env(safe-area-inset-bottom, 0px));
  border-top: 1px solid var(--color-linea);
}

.admin-shell__usuario-pie {
  display: flex;
  align-items: center;
  gap: var(--espacio-md);
  min-width: 0;
}

.admin-shell__usuario-pie .admin-shell__usuario-textos {
  display: flex;
}

/* Uno debajo del otro: lado a lado, en un panel de 85vw, los dos textos
   se partían en dos líneas. */
.admin-shell__acciones-pie {
  display: grid;
  gap: var(--espacio-sm);
}

.admin-shell__salir--pie {
  display: flex;
  justify-content: center;
  min-height: var(--area-tactil-minima);
  text-decoration: none;
}

/* ---- Contenido ---- */
.admin-shell__main {
  width: 100%;
  max-width: var(--ancho-contenido);
  margin: 0 auto;
  padding: var(--espacio-xl) var(--margen-pagina) var(--espacio-4xl);
}

.admin-shell__main:focus {
  outline: none;
}

/* ---- Tableta: el nombre del usuario cabe en la barra ---- */
@media (min-width: 40rem) {
  .admin-shell__usuario-textos {
    display: flex;
  }
}

/* ---- Escritorio: barra lateral fija ---- */
@media (min-width: 64rem) {
  .admin-shell {
    display: grid;
    grid-template-columns: var(--ancho-menu) minmax(0, 1fr);
    grid-template-rows: var(--alto-barra) 1fr;
  }

  .admin-shell__barra {
    grid-column: 2;
    grid-row: 1;
    padding: 0 var(--margen-pagina);
  }

  .admin-shell__boton-menu,
  .admin-shell__marca--barra,
  .admin-shell__cerrar-menu,
  .admin-shell__velo,
  .admin-shell__panel-pie {
    display: none;
  }

  .admin-shell__salir {
    display: inline-flex;
  }

  .admin-shell__panel {
    grid-column: 1;
    grid-row: 1 / span 2;
    position: sticky;
    top: 0;
    height: 100vh;
    height: 100dvh;
    width: auto;
    box-shadow: none;
    border-right: 1px solid var(--color-linea);
    transform: none;
    visibility: visible;
    transition: none;
  }

  .admin-shell__main {
    grid-column: 2;
    grid-row: 2;
    margin: 0;
    padding-top: var(--espacio-3xl);
  }
}
</style>
