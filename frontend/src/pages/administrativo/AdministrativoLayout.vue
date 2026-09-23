<script setup lang="ts">
import { computed } from "vue";

import { useAuthStore } from "@/features/auth/stores/authStore";
import { AdminShell } from "@/shared/components";

const auth = useAuthStore();

const navegacion = computed(() => {
  const items = [
    { a: "/administrativo", etiqueta: "Inicio" },
    { a: "/administrativo/catalogo", etiqueta: "Datos maestros" },
    { a: "/administrativo/estudiantes", etiqueta: "Estudiantes" },
    { a: "/administrativo/encargados", etiqueta: "Encargados" },
    { a: "/administrativo/asignaciones", etiqueta: "Asignaciones" },
  ];
  if (auth.usuario?.role_name === "Dirección") {
    items.push(
      { a: "/administrativo/asistencia", etiqueta: "Asistencia" },
      { a: "/administrativo/justificaciones", etiqueta: "Justificaciones" },
      { a: "/administrativo/plantilla-asistencia", etiqueta: "Plantilla de talleres" },
      { a: "/administrativo/notas/modificaciones", etiqueta: "Modificaciones de notas" },
    );
  }
  return items;
});
</script>

<template>
  <AdminShell :navegacion="navegacion">
    <RouterView />
  </AdminShell>
</template>
