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
  History,
  House,
  Inbox,
  Megaphone,
  ShieldAlert,
  UserCheck,
  UserCog,
  Users,
  Wallet,
} from "lucide-vue-next";
import { AdminShell } from "@/shared/components";
import type { GrupoNavegacion } from "@/shared/components/AdminShell.vue";

// Agrupado por tarea, no por módulo técnico: a Dirección le aparecen 17
// opciones, y en una lista plana no se encontraba nada.
// Agrupado por tarea, no por módulo técnico. Cada opción declara el área
// de docs/permisos-roles.md que consulta y AdminShell la muestra solo si
// el rol la alcanza — ya no hay nombres de rol escritos acá.
const navegacion: GrupoNavegacion[] = [
  { items: [{ a: "/administrativo", etiqueta: "Inicio", icono: House, exacto: true }] },
  {
    titulo: "Estudiantes",
    items: [
      { a: "/administrativo/estudiantes", etiqueta: "Estudiantes", icono: GraduationCap, area: "estudiantes_encargados" },
      { a: "/administrativo/encargados", etiqueta: "Encargados", icono: Users, area: "estudiantes_encargados" },
      { a: "/administrativo/asignaciones", etiqueta: "Asignaciones", icono: UserCheck, area: "horarios_calendario" },
    ],
  },
  {
    titulo: "Asistencia",
    items: [
      { a: "/administrativo/asistencia", etiqueta: "Asistencia", icono: ClipboardCheck, area: "asistencia" },
      { a: "/administrativo/justificaciones", etiqueta: "Justificaciones", icono: FileCheck, area: "asistencia" },
      {
        a: "/administrativo/plantilla-asistencia",
        etiqueta: "Plantilla de talleres",
        icono: FileSpreadsheet,
        area: "asistencia",
        nivel: "editar",
      },
    ],
  },
  {
    titulo: "Notas",
    items: [
      {
        a: "/administrativo/notas/modificaciones",
        etiqueta: "Modificaciones de notas",
        icono: FilePen,
        area: "modificacion_notas",
      },
      { a: "/administrativo/boletines", etiqueta: "Boletines", icono: FileText, area: "notas" },
    ],
  },
  {
    titulo: "Horarios",
    items: [
      { a: "/administrativo/horarios", etiqueta: "Horarios", icono: Clock, area: "horarios_calendario" },
      { a: "/administrativo/calendario", etiqueta: "Calendario", icono: CalendarDays, area: "horarios_calendario" },
    ],
  },
  {
    titulo: "Comunicación",
    items: [
      { a: "/administrativo/avisos", etiqueta: "Avisos", icono: Megaphone, area: "avisos" },
      {
        a: "/administrativo/reportes-conducta",
        etiqueta: "Reportes de conducta",
        icono: ShieldAlert,
        area: "reportes_conducta",
      },
      { a: "/administrativo/buzon", etiqueta: "Buzón", icono: Inbox, area: "buzon" },
    ],
  },
  {
    titulo: "Pagos",
    items: [
      { a: "/administrativo/pagos", etiqueta: "Pagos y solvencia", icono: Wallet, area: "pagos_solvencia" },
      { a: "/administrativo/documentos", etiqueta: "Documentos", icono: FileBadge, area: "documentos" },
    ],
  },
  {
    titulo: "Reportes",
    items: [
      { a: "/administrativo/reportes", etiqueta: "Reportes", icono: ChartColumn, area: "reportes_institucionales" },
      { a: "/administrativo/metricas", etiqueta: "Métricas", icono: Activity, area: "reportes_institucionales" },
    ],
  },
  {
    titulo: "Administración",
    items: [
      { a: "/administrativo/usuarios", etiqueta: "Usuarios", icono: UserCog, area: "usuarios_roles" },
      { a: "/administrativo/catalogo", etiqueta: "Datos maestros", icono: Database, area: "datos_maestros" },
      { a: "/administrativo/bitacora", etiqueta: "Bitácora", icono: History, area: "bitacora_registro_acceso" },
    ],
  },
];
</script>

<template>
  <AdminShell portal="Portal administrativo" :navegacion="navegacion" ruta-cuenta="/administrativo/cuenta">
    <RouterView />
  </AdminShell>
</template>
