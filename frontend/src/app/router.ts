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
    ],
  },
  {
    path: "/operativo",
    name: "operativo-inicio",
    component: () => import("@/pages/operativo/InicioPage.vue"),
    meta: { roles: ROLES_OPERATIVO },
  },
  {
    path: "/portal",
    name: "portal-inicio",
    component: () => import("@/pages/publico/InicioPage.vue"),
    meta: { roles: ROLES_PUBLICO },
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
