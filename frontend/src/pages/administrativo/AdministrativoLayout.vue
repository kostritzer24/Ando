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
  if (["Dirección", "Encargado de pagos"].includes(auth.usuario?.role_name ?? "")) {
    items.push(
      { a: "/administrativo/pagos", etiqueta: "Pagos y solvencia" },
      { a: "/administrativo/documentos", etiqueta: "Documentos" },
    );
  }
  if (auth.usuario?.role_name === "Dirección") {
    items.push(
      { a: "/administrativo/asistencia", etiqueta: "Asistencia" },
      { a: "/administrativo/justificaciones", etiqueta: "Justificaciones" },
      { a: "/administrativo/plantilla-asistencia", etiqueta: "Plantilla de talleres" },
      { a: "/administrativo/notas/modificaciones", etiqueta: "Modificaciones de notas" },
      { a: "/administrativo/boletines", etiqueta: "Boletines" },
      { a: "/administrativo/horarios", etiqueta: "Horarios" },
      { a: "/administrativo/calendario", etiqueta: "Calendario" },
      { a: "/administrativo/avisos", etiqueta: "Avisos" },
      { a: "/administrativo/reportes-conducta", etiqueta: "Reportes de conducta" },
      { a: "/administrativo/buzon", etiqueta: "Buzón" },
      { a: "/administrativo/reportes", etiqueta: "Reportes" },
      { a: "/administrativo/metricas", etiqueta: "Métricas" },
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
