import { defineStore } from "pinia";
import { ref } from "vue";

import { fijarTokenDeAcceso } from "@/app/http";

import { cerrarSesion, iniciarSesion, type Usuario } from "../api/authApi";

export const useAuthStore = defineStore("auth", () => {
  const usuario = ref<Usuario | null>(null);

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

  return { usuario, ingresar, salir };
});
