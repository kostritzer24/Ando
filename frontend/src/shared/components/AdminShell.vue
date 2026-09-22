<script setup lang="ts">
import { useRouter } from "vue-router";

import { useAuthStore } from "@/features/auth/stores/authStore";

defineProps<{
  navegacion: { a: string; etiqueta: string }[];
}>();

const auth = useAuthStore();
const router = useRouter();

async function salir(): Promise<void> {
  await auth.salir();
  router.push({ name: "ingresar" });
}
</script>

<template>
  <div class="admin-shell">
    <aside class="admin-shell__nav">
      <div class="admin-shell__marca">El Patojismo</div>
      <nav aria-label="Navegación principal">
        <RouterLink
          v-for="item in navegacion"
          :key="item.a"
          :to="item.a"
          class="admin-shell__enlace"
          active-class="admin-shell__enlace--activo"
        >
          {{ item.etiqueta }}
        </RouterLink>
      </nav>
    </aside>
    <div class="admin-shell__contenido">
      <header class="admin-shell__topbar">
        <span class="admin-shell__usuario">
          {{ auth.usuario?.first_name || auth.usuario?.username }} · {{ auth.usuario?.role_name }}
        </span>
        <button type="button" class="admin-shell__salir" @click="salir">Cerrar sesión</button>
      </header>
      <main class="admin-shell__main">
        <slot />
      </main>
    </div>
  </div>
</template>

<style scoped>
.admin-shell {
  display: flex;
  min-height: 100vh;
}

.admin-shell__nav {
  flex: none;
  width: 15rem;
  background: var(--color-papel);
  border-right: 1px solid var(--color-linea);
  padding: var(--espacio-lg) 0;
  display: flex;
  flex-direction: column;
  gap: var(--espacio-lg);
}

.admin-shell__marca {
  font-family: var(--fuente-titulo);
  font-weight: 800;
  font-size: var(--texto-md);
  padding: 0 var(--espacio-xl);
  color: var(--color-accion);
}

.admin-shell__enlace {
  display: block;
  min-height: var(--area-tactil-minima);
  display: flex;
  align-items: center;
  padding: 0 var(--espacio-xl);
  font-size: var(--texto-base);
  color: var(--color-tinta);
  text-decoration: none;
  border-left: 3px solid transparent;
}

.admin-shell__enlace:hover {
  background: var(--color-fondo);
}

.admin-shell__enlace--activo {
  border-left-color: var(--color-accion);
  color: var(--color-accion);
  font-weight: 600;
  background: var(--color-fondo);
}

.admin-shell__contenido {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.admin-shell__topbar {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--espacio-lg);
  padding: var(--espacio-md) var(--espacio-xl);
  border-bottom: 1px solid var(--color-linea);
  background: var(--color-papel);
}

.admin-shell__usuario {
  font-size: var(--texto-sm);
  color: var(--color-tinta-suave);
}

.admin-shell__salir {
  min-height: 2.2rem;
  padding: 0 0.75rem;
  background: none;
  border: 1px solid var(--color-linea);
  border-radius: var(--radio-sm);
  font-size: var(--texto-sm);
  font-weight: 600;
  color: var(--color-accion);
  cursor: pointer;
}

.admin-shell__salir:focus-visible {
  outline: 2px solid var(--color-accion);
  outline-offset: 2px;
}

.admin-shell__main {
  flex: 1;
  padding: var(--espacio-xl);
  max-width: 64rem;
  width: 100%;
}
</style>
