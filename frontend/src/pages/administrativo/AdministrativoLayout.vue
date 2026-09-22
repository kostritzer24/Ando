<script setup lang="ts">
import { AdminShell } from "@/shared/components";

const navegacion = [
  { a: "/administrativo", etiqueta: "Inicio" },
  { a: "/administrativo/catalogo", etiqueta: "Datos maestros" },
  { a: "/administrativo/estudiantes", etiqueta: "Estudiantes" },
  { a: "/administrativo/encargados", etiqueta: "Encargados" },
  { a: "/administrativo/asignaciones", etiqueta: "Asignaciones" },
];
</script>

<template>
  <AdminShell :navegacion="navegacion">
    <RouterView />
  </AdminShell>
</template>
