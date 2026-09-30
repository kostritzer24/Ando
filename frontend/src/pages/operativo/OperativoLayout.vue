<script setup lang="ts">
import {
  CalendarDays,
  ClipboardCheck,
  Clock,
  FileCheck,
  FilePen,
  FileSpreadsheet,
  House,
  Inbox,
  Megaphone,
  NotebookPen,
  ShieldAlert,
  Upload,
} from "lucide-vue-next";
import { computed } from "vue";

import { useAuthStore } from "@/features/auth/stores/authStore";
import { AdminShell } from "@/shared/components";
import type { GrupoNavegacion } from "@/shared/components/AdminShell.vue";

const auth = useAuthStore();

// Cada opción declara su área de docs/permisos-roles.md; AdminShell la
// filtra con la matriz del rol. Tallerista no ve Notas porque su rol no
// tiene esa área (ADR-0001: los talleres no califican), y solo el maestro
// guía tiene Reportes de conducta y Buzón.
const navegacion = computed<GrupoNavegacion[]>(() => [
  { items: [{ a: "/operativo", etiqueta: "Inicio", icono: House, exacto: true }] },
  {
    titulo: "Asistencia",
    items: [
      { a: "/operativo/asistencia", etiqueta: "Asistencia", icono: ClipboardCheck, area: "asistencia" },
      { a: "/operativo/justificaciones", etiqueta: "Justificaciones", icono: FileCheck, area: "asistencia" },
      {
        a: "/operativo/plantilla-asistencia",
        etiqueta: "Plantilla de talleres",
        icono: FileSpreadsheet,
        area: "asistencia",
        nivel: "editar",
        // La plantilla es de asistencia de talleres: es del tallerista,
        // no de cualquiera que registre asistencia.
        visible: auth.usuario?.role_name === "Tallerista",
      },
    ],
  },
  {
    titulo: "Notas",
    items: [
      { a: "/operativo/notas/unidad", etiqueta: "Diseñar unidad", icono: NotebookPen, area: "notas", nivel: "editar" },
      { a: "/operativo/notas/capturar", etiqueta: "Capturar notas", icono: FilePen, area: "notas", nivel: "editar" },
      { a: "/operativo/notas/plantilla", etiqueta: "Plantilla de notas", icono: Upload, area: "notas", nivel: "editar" },
      { a: "/operativo/notas/modificaciones", etiqueta: "Modificaciones", icono: FileCheck, area: "notas", nivel: "editar" },
    ],
  },
  {
    titulo: "Horarios",
    items: [
      { a: "/operativo/mi-horario", etiqueta: "Mi horario", icono: Clock, area: "horarios_calendario" },
      { a: "/operativo/calendario", etiqueta: "Calendario", icono: CalendarDays, area: "horarios_calendario" },
    ],
  },
  {
    titulo: "Comunicación",
    items: [
      { a: "/operativo/avisos", etiqueta: "Avisos", icono: Megaphone, area: "avisos" },
      {
        a: "/operativo/reportes-conducta",
        etiqueta: "Reportes de conducta",
        icono: ShieldAlert,
        area: "reportes_conducta",
        nivel: "editar",
      },
      { a: "/operativo/buzon", etiqueta: "Buzón", icono: Inbox, area: "buzon", nivel: "editar" },
    ],
  },
]);
</script>

<template>
  <AdminShell portal="Portal operativo" :navegacion="navegacion" ruta-cuenta="/operativo/cuenta">
    <RouterView />
  </AdminShell>
</template>
