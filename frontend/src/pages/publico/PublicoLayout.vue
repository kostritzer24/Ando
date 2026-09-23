<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { useAuthStore } from "@/features/auth/stores/authStore";
import { usePortalStore } from "@/features/portal/stores/portalStore";
import { AppModal, BottomTabBar, ErrorBanner, ListRow, TopAppBar } from "@/shared/components";

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
  { valor: "/portal", etiqueta: "Inicio" },
  { valor: "/portal/notas", etiqueta: "Notas" },
  { valor: "/portal/asistencia", etiqueta: "Asistencia" },
  { valor: "/portal/pagos", etiqueta: "Pagos" },
  { valor: "/portal/avisos", etiqueta: "Avisos" },
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
    <p v-else-if="portal.cargando" class="portal-layout__cargando">Cargando…</p>

    <template v-else>
      <TopAppBar
        :nombre-estudiante="nombreEstudiante"
        :nombre-seccion="portal.seccionPrincipal"
        @cambiar-estudiante="modalAbierto = true"
      >
        <template #marca>El Patojismo</template>
      </TopAppBar>

      <button type="button" class="portal-layout__salir" @click="salir">Cerrar sesión</button>

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
.portal-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  max-width: 30rem;
  margin: 0 auto;
}

.portal-layout__cargando {
  padding: var(--espacio-xl);
}

.portal-layout__contenido {
  flex: 1;
  padding: var(--espacio-lg) var(--espacio-xl);
  overflow-y: auto;
}

.portal-layout__salir {
  align-self: flex-end;
  margin: var(--espacio-sm) var(--espacio-xl) 0 0;
  background: none;
  border: none;
  color: var(--color-tinta-suave);
  font-size: var(--texto-sm);
  cursor: pointer;
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
