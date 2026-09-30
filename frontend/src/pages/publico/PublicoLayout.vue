<script setup lang="ts">
import { BookOpen, ClipboardCheck, House, LogOut, Megaphone, Wallet } from "lucide-vue-next";
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { useAuthStore } from "@/features/auth/stores/authStore";
import { usePortalStore } from "@/features/portal/stores/portalStore";
import { AppModal, BottomTabBar, CargandoBloque, ErrorBanner, ListRow, TopAppBar } from "@/shared/components";

const auth = useAuthStore();
const portal = usePortalStore();
const route = useRoute();
const router = useRouter();

const modalAbierto = ref(false);

const nombreEstudiante = computed(() => {
  const e = portal.estudianteSeleccionado;
  return e ? `${e.first_name} ${e.last_name}` : "";
});

const pestanas = [
  { valor: "/portal", etiqueta: "Inicio", icono: House },
  { valor: "/portal/notas", etiqueta: "Notas", icono: BookOpen },
  { valor: "/portal/asistencia", etiqueta: "Asistencia", icono: ClipboardCheck },
  { valor: "/portal/pagos", etiqueta: "Pagos", icono: Wallet },
  { valor: "/portal/avisos", etiqueta: "Avisos", icono: Megaphone },
];

function elegir(publicId: string): void {
  portal.elegirEstudiante(publicId);
  modalAbierto.value = false;
}

async function salir(): Promise<void> {
  await auth.salir();
  router.push({ name: "ingresar" });
}

onMounted(() => {
  if (portal.estudiantes.length === 0) {
    portal.cargarEstudiantes();
  }
});
</script>

<template>
  <div class="portal-layout">
    <ErrorBanner v-if="portal.error" :mensaje="portal.error" etiqueta-accion="Reintentar" @accion="portal.cargarEstudiantes" />
    <div v-else-if="portal.cargando" class="portal-layout__cargando"><CargandoBloque :filas="3" /></div>

    <template v-else>
      <TopAppBar
        :nombre-estudiante="nombreEstudiante"
        :nombre-seccion="portal.seccionPrincipal"
        @cambiar-estudiante="modalAbierto = true"
      >
        <template #marca><img src="/marca.png" alt="" width="24" height="24" /></template>
        <template #acciones>
          <button type="button" class="portal-layout__salir" @click="salir">
            <LogOut aria-hidden="true" />
            Cerrar sesión
          </button>
        </template>
      </TopAppBar>

      <main class="portal-layout__contenido">
        <RouterView />
      </main>

      <BottomTabBar
        :items="pestanas"
        :model-value="route.path"
        @update:model-value="(valor) => router.push(valor)"
      />
    </template>

    <AppModal v-if="modalAbierto" titulo="Cambiar estudiante" @cerrar="modalAbierto = false">
      <button
        v-for="estudiante in portal.estudiantes"
        :key="estudiante.public_id"
        type="button"
        class="portal-layout__opcion-estudiante"
        @click="elegir(estudiante.public_id)"
      >
        <ListRow>
          {{ estudiante.first_name }} {{ estudiante.last_name }}
          <template #final>{{ estudiante.internal_code }}</template>
        </ListRow>
      </button>
    </AppModal>
  </div>
</template>

<style scoped>
/* Mobile-first (RNF-01): una columna de teléfono. En pantallas grandes
   se queda en esa columna, centrada, en vez de estirarse. */
.portal-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  min-height: 100dvh;
  max-width: 30rem;
  margin: 0 auto;
  background: var(--color-papel);
}

@media (min-width: 40rem) {
  .portal-layout {
    border-left: 1px solid var(--color-linea);
    border-right: 1px solid var(--color-linea);
  }
}

.portal-layout__cargando {
  padding: var(--espacio-xl);
}

.portal-layout__contenido {
  flex: 1;
  padding: var(--espacio-xl) var(--espacio-lg) var(--espacio-3xl);
}

.portal-layout__salir {
  display: inline-flex;
  align-items: center;
  gap: var(--espacio-xs);
  min-height: var(--area-tactil-minima);
  padding: 0 var(--espacio-xs);
  background: none;
  border: none;
  color: var(--color-tinta-suave);
  font-size: var(--texto-sm);
  font-weight: 500;
  cursor: pointer;
}

.portal-layout__salir svg {
  width: 1rem;
  height: 1rem;
}

.portal-layout__opcion-estudiante {
  display: block;
  width: 100%;
  background: none;
  border: none;
  text-align: left;
  cursor: pointer;
  font-family: var(--fuente-cuerpo);
  font-size: var(--texto-base);
  color: var(--color-tinta);
}
</style>
