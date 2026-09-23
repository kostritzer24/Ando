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
  // ADR-0001: los talleres no califican — Tallerista nunca tiene "notas".
  if (["Docente", "Docente con sección a cargo"].includes(auth.usuario?.role_name ?? "")) {
    items.push(
      { a: "/operativo/notas/unidad", etiqueta: "Diseñar unidad" },
      { a: "/operativo/notas/capturar", etiqueta: "Capturar notas" },
      { a: "/operativo/notas/plantilla", etiqueta: "Plantilla de notas" },
      { a: "/operativo/notas/modificaciones", etiqueta: "Modificaciones" },
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
