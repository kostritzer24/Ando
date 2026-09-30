<script setup lang="ts">
import {
  Activity,
  CalendarDays,
  ChartColumn,
  ClipboardCheck,
  Clock,
  Database,
  FileBadge,
  FileCheck,
  FilePen,
  FileSpreadsheet,
  FileText,
  GraduationCap,
  House,
  Inbox,
  Megaphone,
  ShieldAlert,
  UserCheck,
  Users,
  Wallet,
} from "lucide-vue-next";
import { computed } from "vue";

import { useAuthStore } from "@/features/auth/stores/authStore";
import { AdminShell } from "@/shared/components";
import type { GrupoNavegacion } from "@/shared/components/AdminShell.vue";

const auth = useAuthStore();

// Agrupado por tarea, no por módulo técnico: a Dirección le aparecen 17
// opciones, y en una lista plana no se encontraba nada.
const navegacion = computed<GrupoNavegacion[]>(() => {
  const rol = auth.usuario?.role_name ?? "";
  const esDireccion = rol === "Dirección";
  const vePagos = ["Dirección", "Encargado de pagos"].includes(rol);

  const grupos: GrupoNavegacion[] = [
    { items: [{ a: "/administrativo", etiqueta: "Inicio", icono: House, exacto: true }] },
    {
      titulo: "Estudiantes",
      items: [
        { a: "/administrativo/estudiantes", etiqueta: "Estudiantes", icono: GraduationCap },
        { a: "/administrativo/encargados", etiqueta: "Encargados", icono: Users },
        { a: "/administrativo/asignaciones", etiqueta: "Asignaciones", icono: UserCheck },
      ],
    },
  ];

  if (esDireccion) {
    grupos.push(
      {
        titulo: "Asistencia",
        items: [
          { a: "/administrativo/asistencia", etiqueta: "Asistencia", icono: ClipboardCheck },
          { a: "/administrativo/justificaciones", etiqueta: "Justificaciones", icono: FileCheck },
          { a: "/administrativo/plantilla-asistencia", etiqueta: "Plantilla de talleres", icono: FileSpreadsheet },
        ],
      },
      {
        titulo: "Notas",
        items: [
          { a: "/administrativo/notas/modificaciones", etiqueta: "Modificaciones de notas", icono: FilePen },
          { a: "/administrativo/boletines", etiqueta: "Boletines", icono: FileText },
        ],
      },
      {
        titulo: "Horarios",
        items: [
          { a: "/administrativo/horarios", etiqueta: "Horarios", icono: Clock },
          { a: "/administrativo/calendario", etiqueta: "Calendario", icono: CalendarDays },
        ],
      },
      {
        titulo: "Comunicación",
        items: [
          { a: "/administrativo/avisos", etiqueta: "Avisos", icono: Megaphone },
          { a: "/administrativo/reportes-conducta", etiqueta: "Reportes de conducta", icono: ShieldAlert },
          { a: "/administrativo/buzon", etiqueta: "Buzón", icono: Inbox },
        ],
      },
    );
  }

  if (vePagos) {
    grupos.push({
      titulo: "Pagos",
      items: [
        { a: "/administrativo/pagos", etiqueta: "Pagos y solvencia", icono: Wallet },
        { a: "/administrativo/documentos", etiqueta: "Documentos", icono: FileBadge },
      ],
    });
  }

  if (esDireccion) {
    grupos.push({
      titulo: "Reportes",
      items: [
        { a: "/administrativo/reportes", etiqueta: "Reportes", icono: ChartColumn },
        { a: "/administrativo/metricas", etiqueta: "Métricas", icono: Activity },
      ],
    });
  }

  grupos.push({
    titulo: "Configuración",
    items: [{ a: "/administrativo/catalogo", etiqueta: "Datos maestros", icono: Database }],
  });

  return grupos;
});
</script>

<template>
  <AdminShell portal="Portal administrativo" :navegacion="navegacion">
    <RouterView />
  </AdminShell>
</template>
