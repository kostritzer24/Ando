<script setup lang="ts">
import { computed } from "vue";

import { useAuthStore } from "@/features/auth/stores/authStore";
import { AdminShell } from "@/shared/components";

const auth = useAuthStore();

const navegacion = computed(() => {
  const items = [
    { a: "/operativo", etiqueta: "Inicio" },
    { a: "/operativo/asistencia", etiqueta: "Asistencia" },
    { a: "/operativo/justificaciones", etiqueta: "Justificaciones" },
  ];
  if (auth.usuario?.role_name === "Tallerista") {
    items.push({ a: "/operativo/plantilla-asistencia", etiqueta: "Plantilla de talleres" });
  }
  return items;
});
</script>

<template>
  <AdminShell :navegacion="navegacion">
    <RouterView />
  </AdminShell>
</template>
