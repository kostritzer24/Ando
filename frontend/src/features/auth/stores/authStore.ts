import { defineStore } from "pinia";
import { ref } from "vue";

import { fijarTokenDeAcceso } from "@/app/http";

import { cerrarSesion, iniciarSesion, obtenerPerfil, refrescarToken, type Usuario } from "../api/authApi";

export const useAuthStore = defineStore("auth", () => {
  const usuario = ref<Usuario | null>(null);
  // El token de acceso vive solo en memoria (sección 14.1) — nunca en
  // localStorage. Eso significa que recargar la página, o abrir un
  // enlace directo, lo pierde. `restaurarSesion` es lo que reconstruye
  // la sesión a partir de la cookie HttpOnly del token de refresco,
  // antes de que el guard del router decida a dónde mandar a la persona.
  const restaurandoSesion = ref(true);

  async function ingresar(username: string, password: string): Promise<Usuario> {
    const { access, user } = await iniciarSesion(username, password);
    fijarTokenDeAcceso(access);
    usuario.value = user;
    return user;
  }

  async function salir(): Promise<void> {
    await cerrarSesion();
    fijarTokenDeAcceso(null);
    usuario.value = null;
  }

  async function restaurarSesion(): Promise<void> {
    try {
      const access = await refrescarToken();
      fijarTokenDeAcceso(access);
      usuario.value = await obtenerPerfil();
    } catch {
      // No hay cookie de refresco válida — no es un error, es la
      // situación normal de alguien que no tiene sesión iniciada.
      fijarTokenDeAcceso(null);
      usuario.value = null;
    } finally {
      restaurandoSesion.value = false;
    }
  }

  return { usuario, restaurandoSesion, ingresar, salir, restaurarSesion };
});
