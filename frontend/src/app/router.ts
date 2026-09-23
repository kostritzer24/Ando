import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";

import {
  articulosConvivenciaApi,
  becasApi,
  cursosApi,
  tiposActividadApi,
  tiposDocumentoApi,
  tiposJustificacionApi,
} from "@/features/catalogo/api/catalogoApi";
import {
  CONFIG_ARTICULOS_CONVIVENCIA,
  CONFIG_BECAS,
  CONFIG_CURSOS,
  CONFIG_TIPOS_ACTIVIDAD,
  CONFIG_TIPOS_DOCUMENTO,
  CONFIG_TIPOS_JUSTIFICACION,
} from "@/features/catalogo/config/campos";
import { useAuthStore } from "@/features/auth/stores/authStore";
import { comoRecursoGenerico } from "@/shared/api/resource";

const catalogoConfigs = {
  cursos: CONFIG_CURSOS,
  tiposActividad: CONFIG_TIPOS_ACTIVIDAD,
  tiposJustificacion: CONFIG_TIPOS_JUSTIFICACION,
  tiposDocumento: CONFIG_TIPOS_DOCUMENTO,
  becas: CONFIG_BECAS,
  articulosConvivencia: CONFIG_ARTICULOS_CONVIVENCIA,
};

const catalogoRecursos = {
  cursos: comoRecursoGenerico(cursosApi),
  tiposActividad: comoRecursoGenerico(tiposActividadApi),
  tiposJustificacion: comoRecursoGenerico(tiposJustificacionApi),
  tiposDocumento: comoRecursoGenerico(tiposDocumentoApi),
  becas: comoRecursoGenerico(becasApi),
  articulosConvivencia: comoRecursoGenerico(articulosConvivenciaApi),
};

const ROLES_ADMINISTRATIVO = [
  "Dirección",
  "Coordinación",
  "Encargado de pagos",
  "Administrador del sistema",
];
const ROLES_OPERATIVO = ["Docente", "Docente con sección a cargo", "Tallerista"];
const ROLES_PUBLICO = ["Padre de familia"];

export const DESTINO_POR_ROL: Record<string, string> = {
  Dirección: "/administrativo",
  Coordinación: "/administrativo",
  "Encargado de pagos": "/administrativo",
  "Administrador del sistema": "/administrativo",
  Docente: "/operativo",
  "Docente con sección a cargo": "/operativo",
  Tallerista: "/operativo",
  "Padre de familia": "/portal",
};

const routes: RouteRecordRaw[] = [
  {
    path: "/ingresar",
    name: "ingresar",
    component: () => import("@/features/auth/components/LoginPage.vue"),
    meta: { publica: true },
  },
  {
    path: "/cambiar-contrasena",
    name: "cambiar-contrasena",
    component: () => import("@/features/auth/components/ChangePasswordPage.vue"),
    meta: { requiereSesion: true },
  },
  {
    path: "/administrativo",
    component: () => import("@/pages/administrativo/AdministrativoLayout.vue"),
    meta: { roles: ROLES_ADMINISTRATIVO },
    children: [
      {
        path: "",
        name: "administrativo-inicio",
        component: () => import("@/pages/administrativo/InicioPage.vue"),
      },
      {
        path: "catalogo",
        name: "catalogo-index",
        component: () => import("@/features/catalogo/components/CatalogoIndexPage.vue"),
      },
      {
        path: "catalogo/ciclos",
        name: "catalogo-ciclos",
        component: () => import("@/features/catalogo/components/CiclosPage.vue"),
      },
      {
        path: "catalogo/secciones",
        name: "catalogo-secciones",
        component: () => import("@/features/catalogo/components/SeccionesPage.vue"),
      },
      {
        path: "catalogo/cursos",
        name: "catalogo-cursos",
        component: () => import("@/features/catalogo/components/CatalogoSimplePage.vue"),
        props: () => ({
          config: catalogoConfigs.cursos,
          recurso: catalogoRecursos.cursos,
        }),
      },
      {
        path: "catalogo/tipos-actividad",
        name: "catalogo-tipos-actividad",
        component: () => import("@/features/catalogo/components/CatalogoSimplePage.vue"),
        props: () => ({
          config: catalogoConfigs.tiposActividad,
          recurso: catalogoRecursos.tiposActividad,
        }),
      },
      {
        path: "catalogo/tipos-justificacion",
        name: "catalogo-tipos-justificacion",
        component: () => import("@/features/catalogo/components/CatalogoSimplePage.vue"),
        props: () => ({
          config: catalogoConfigs.tiposJustificacion,
          recurso: catalogoRecursos.tiposJustificacion,
        }),
      },
      {
        path: "catalogo/tipos-documento",
        name: "catalogo-tipos-documento",
        component: () => import("@/features/catalogo/components/CatalogoSimplePage.vue"),
        props: () => ({
          config: catalogoConfigs.tiposDocumento,
          recurso: catalogoRecursos.tiposDocumento,
        }),
      },
      {
        path: "catalogo/becas",
        name: "catalogo-becas",
        component: () => import("@/features/catalogo/components/CatalogoSimplePage.vue"),
        props: () => ({
          config: catalogoConfigs.becas,
          recurso: catalogoRecursos.becas,
        }),
      },
      {
        path: "catalogo/articulos-convivencia",
        name: "catalogo-articulos-convivencia",
        component: () => import("@/features/catalogo/components/CatalogoSimplePage.vue"),
        props: () => ({
          config: catalogoConfigs.articulosConvivencia,
          recurso: catalogoRecursos.articulosConvivencia,
        }),
      },
      {
        path: "estudiantes",
        name: "estudiantes",
        component: () => import("@/features/estudiantes/components/EstudiantesPage.vue"),
      },
      {
        path: "estudiantes/:publicId",
        name: "expediente",
        component: () => import("@/features/estudiantes/components/ExpedientePage.vue"),
      },
      {
        path: "encargados",
        name: "encargados",
        component: () => import("@/features/estudiantes/components/EncargadosPage.vue"),
      },
      {
        path: "asignaciones",
        name: "asignaciones",
        component: () => import("@/features/asignaciones/components/AsignacionesPage.vue"),
      },
      {
        path: "plantilla-asistencia",
        name: "administrativo-plantilla-asistencia",
        component: () => import("@/features/asistencia/components/PlantillaAsistenciaPage.vue"),
      },
      {
        path: "asistencia",
        name: "administrativo-asistencia",
        component: () => import("@/features/asistencia/components/TomarAsistenciaPage.vue"),
      },
      {
        path: "justificaciones",
        name: "administrativo-justificaciones",
        component: () => import("@/features/asistencia/components/JustificacionesPage.vue"),
      },
      {
        path: "notas/modificaciones",
        name: "administrativo-notas-modificaciones",
        component: () => import("@/features/notas/components/ModificacionesPage.vue"),
      },
      {
        path: "pagos",
        name: "administrativo-pagos",
        component: () => import("@/features/pagos/components/PagosPage.vue"),
      },
      {
        path: "documentos",
        name: "administrativo-documentos",
        component: () => import("@/features/pagos/components/DocumentosPage.vue"),
      },
      {
        path: "boletines",
        name: "administrativo-boletines",
        component: () => import("@/features/pagos/components/BoletinesPage.vue"),
      },
      {
        path: "horarios",
        name: "administrativo-horarios",
        component: () => import("@/features/horarios/components/HorarioGridPage.vue"),
      },
      {
        path: "calendario",
        name: "administrativo-calendario",
        component: () => import("@/features/horarios/components/CalendarioPage.vue"),
      },
      {
        path: "avisos",
        name: "administrativo-avisos",
        component: () => import("@/features/comunicacion/components/AvisosPage.vue"),
      },
      {
        path: "reportes-conducta",
        name: "administrativo-reportes-conducta",
        component: () => import("@/features/comunicacion/components/ReportesConductaPage.vue"),
      },
      {
        path: "buzon",
        name: "administrativo-buzon",
        component: () => import("@/features/comunicacion/components/BuzonPage.vue"),
      },
      {
        path: "reportes",
        name: "administrativo-reportes",
        component: () => import("@/features/reportes/components/ReportesPage.vue"),
      },
      {
        path: "metricas",
        name: "administrativo-metricas",
        component: () => import("@/features/reportes/components/MetricasPage.vue"),
      },
    ],
  },
  {
    path: "/operativo",
    component: () => import("@/pages/operativo/OperativoLayout.vue"),
    meta: { roles: ROLES_OPERATIVO },
    children: [
      {
        path: "",
        name: "operativo-inicio",
        component: () => import("@/pages/operativo/InicioPage.vue"),
      },
      {
        path: "asistencia",
        name: "operativo-asistencia",
        component: () => import("@/features/asistencia/components/TomarAsistenciaPage.vue"),
      },
      {
        path: "justificaciones",
        name: "operativo-justificaciones",
        component: () => import("@/features/asistencia/components/JustificacionesPage.vue"),
      },
      {
        path: "plantilla-asistencia",
        name: "operativo-plantilla-asistencia",
        component: () => import("@/features/asistencia/components/PlantillaAsistenciaPage.vue"),
      },
      {
        path: "notas/unidad",
        name: "operativo-notas-unidad",
        component: () => import("@/features/notas/components/UnidadPage.vue"),
      },
      {
        path: "notas/capturar",
        name: "operativo-notas-capturar",
        component: () => import("@/features/notas/components/CapturarNotasPage.vue"),
      },
      {
        path: "notas/plantilla",
        name: "operativo-notas-plantilla",
        component: () => import("@/features/notas/components/PlantillaNotasPage.vue"),
      },
      {
        path: "notas/modificaciones",
        name: "operativo-notas-modificaciones",
        component: () => import("@/features/notas/components/ModificacionesPage.vue"),
      },
      {
        path: "mi-horario",
        name: "operativo-mi-horario",
        component: () => import("@/features/horarios/components/MiHorarioPage.vue"),
      },
      {
        path: "calendario",
        name: "operativo-calendario",
        component: () => import("@/features/horarios/components/CalendarioPage.vue"),
      },
      {
        path: "avisos",
        name: "operativo-avisos",
        component: () => import("@/features/comunicacion/components/AvisosPage.vue"),
      },
      {
        path: "reportes-conducta",
        name: "operativo-reportes-conducta",
        component: () => import("@/features/comunicacion/components/ReportesConductaPage.vue"),
      },
      {
        path: "buzon",
        name: "operativo-buzon",
        component: () => import("@/features/comunicacion/components/BuzonPage.vue"),
      },
    ],
  },
  {
    path: "/portal",
    component: () => import("@/pages/publico/PublicoLayout.vue"),
    meta: { roles: ROLES_PUBLICO },
    children: [
      {
        path: "",
        name: "portal-inicio",
        component: () => import("@/features/portal/components/InicioPage.vue"),
      },
      {
        path: "notas",
        name: "portal-notas",
        component: () => import("@/features/portal/components/NotasPage.vue"),
      },
      {
        path: "asistencia",
        name: "portal-asistencia",
        component: () => import("@/features/portal/components/AsistenciaPage.vue"),
      },
      {
        path: "pagos",
        name: "portal-pagos",
        component: () => import("@/features/portal/components/PagosPage.vue"),
      },
      {
        path: "avisos",
        name: "portal-avisos",
        component: () => import("@/features/portal/components/AvisosPage.vue"),
      },
    ],
  },
  {
    path: "/verificar/:codigo",
    name: "verificar-documento",
    component: () => import("@/features/documentos/components/VerificarPage.vue"),
    meta: { publica: true },
  },
  { path: "/", redirect: "/ingresar" },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to) => {
  const auth = useAuthStore();

  // Con la sesión restaurada desde la cookie de refresco al arrancar la
  // app (`main.ts`), entrar a /ingresar ya con sesión activa no debe
  // mostrar el formulario de nuevo — manda directo al portal que le toca.
  if (to.name === "ingresar" && auth.usuario) {
    return { path: DESTINO_POR_ROL[auth.usuario.role_name] ?? "/" };
  }

  if (to.meta.publica) {
    return true;
  }
  if (!auth.usuario) {
    return { name: "ingresar" };
  }
  if (to.meta.requiereSesion) {
    return true;
  }

  const rolesPermitidos = to.meta.roles as string[] | undefined;
  if (rolesPermitidos && !rolesPermitidos.includes(auth.usuario.role_name)) {
    return { path: DESTINO_POR_ROL[auth.usuario.role_name] ?? "/ingresar" };
  }
  return true;
});

export default router;
