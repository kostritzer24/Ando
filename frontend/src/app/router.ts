import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";

import { useAuthStore } from "@/features/auth/stores/authStore";

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
    name: "administrativo-inicio",
    component: () => import("@/pages/administrativo/InicioPage.vue"),
    meta: { roles: ROLES_ADMINISTRATIVO },
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
