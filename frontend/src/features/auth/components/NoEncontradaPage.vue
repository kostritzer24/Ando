<script setup lang="ts">
import { computed } from "vue";

import { DESTINO_POR_ROL } from "@/app/router";
import { useAuthStore } from "@/features/auth/stores/authStore";
import { EmptyState } from "@/shared/components";

const auth = useAuthStore();
const inicio = computed(() => DESTINO_POR_ROL[auth.usuario?.role_name ?? ""] ?? "/ingresar");
</script>

<template>
  <main class="no-encontrada">
    <EmptyState
      titulo="Esta página no existe"
      descripcion="Puede que el enlace esté incompleto o que la página ya no esté disponible."
    />
    <RouterLink :to="inicio" class="no-encontrada__volver">Volver al inicio</RouterLink>
  </main>
</template>

<style scoped>
.no-encontrada {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--espacio-lg);
  max-width: 32rem;
  margin: var(--espacio-3xl) auto;
  padding: 0 var(--espacio-lg);
}

.no-encontrada__volver {
  color: var(--color-acento, inherit);
  font-weight: 600;
}
</style>
