<script setup lang="ts">
import { AdminShell } from "@/shared/components";

const navegacion = [
  { a: "/administrativo", etiqueta: "Inicio" },
  { a: "/administrativo/catalogo", etiqueta: "Datos maestros" },
];
</script>

<template>
  <AdminShell :navegacion="navegacion">
    <RouterView />
  </AdminShell>
</template>
