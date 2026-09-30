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

const navegacion = computed<GrupoNavegacion[]>(() => {
  const rol = auth.usuario?.role_name ?? "";

  const asistencia: GrupoNavegacion = {
    titulo: "Asistencia",
    items: [
      { a: "/operativo/asistencia", etiqueta: "Asistencia", icono: ClipboardCheck },
      { a: "/operativo/justificaciones", etiqueta: "Justificaciones", icono: FileCheck },
    ],
  };
  if (rol === "Tallerista") {
    asistencia.items.push({
      a: "/operativo/plantilla-asistencia",
      etiqueta: "Plantilla de talleres",
      icono: FileSpreadsheet,
    });
  }

  const grupos: GrupoNavegacion[] = [
    { items: [{ a: "/operativo", etiqueta: "Inicio", icono: House, exacto: true }] },
    asistencia,
  ];

  // ADR-0001: los talleres no califican — Tallerista nunca tiene "notas".
  if (["Docente", "Docente con sección a cargo"].includes(rol)) {
    grupos.push({
      titulo: "Notas",
      items: [
        { a: "/operativo/notas/unidad", etiqueta: "Diseñar unidad", icono: NotebookPen },
        { a: "/operativo/notas/capturar", etiqueta: "Capturar notas", icono: FilePen },
        { a: "/operativo/notas/plantilla", etiqueta: "Plantilla de notas", icono: Upload },
        { a: "/operativo/notas/modificaciones", etiqueta: "Modificaciones", icono: FileCheck },
      ],
    });
  }

  grupos.push({
    titulo: "Horarios",
    items: [
      { a: "/operativo/mi-horario", etiqueta: "Mi horario", icono: Clock },
      { a: "/operativo/calendario", etiqueta: "Calendario", icono: CalendarDays },
    ],
  });

  const comunicacion: GrupoNavegacion = {
    titulo: "Comunicación",
    items: [{ a: "/operativo/avisos", etiqueta: "Avisos", icono: Megaphone }],
  };
  // Solo el maestro guía tiene alcance de "editar" en reportes de
  // conducta y buzón (docs/permisos-roles.md) — Docente/Tallerista solo
  // ven avisos.
  if (rol === "Docente con sección a cargo") {
    comunicacion.items.push(
      { a: "/operativo/reportes-conducta", etiqueta: "Reportes de conducta", icono: ShieldAlert },
      { a: "/operativo/buzon", etiqueta: "Buzón", icono: Inbox },
    );
  }
  grupos.push(comunicacion);

  return grupos;
});
</script>

<template>
  <AdminShell portal="Portal operativo" :navegacion="navegacion">
    <RouterView />
  </AdminShell>
</template>
