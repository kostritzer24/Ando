import { defineStore } from "pinia";
import { ref } from "vue";

import { alRenovarElToken, fijarTokenDeAcceso, http } from "@/app/http";

import { cerrarSesion, iniciarSesion, obtenerPerfil, refrescarToken, type Usuario } from "../api/authApi";

const CLAVE_CAMBIO_DE_SESION = "ando:cambio-de-sesion";

export const useAuthStore = defineStore("auth", () => {
  const usuario = ref<Usuario | null>(null);
  // El token de acceso vive solo en memoria (sección 14.1) — nunca en
  // localStorage. Eso significa que recargar la página, o abrir un
  // enlace directo, lo pierde. `restaurarSesion` es lo que reconstruye
  // la sesión a partir de la cookie HttpOnly del token de refresco,
  // antes de que el guard del router decida a dónde mandar a la persona.
  const restaurandoSesion = ref(true);

  // Avisa a las demás ventanas del mismo navegador que la sesión cambió
  // (comparten la cookie de refresco, ver `alRenovarElToken`).
  function avisarCambioDeSesion(): void {
    try {
      localStorage.setItem(CLAVE_CAMBIO_DE_SESION, String(Date.now()));
    } catch {
      // Sin almacenamiento disponible no se avisa; el resto funciona igual.
    }
  }

  async function ingresar(username: string, password: string): Promise<Usuario> {
    const { access, user } = await iniciarSesion(username, password);
    fijarTokenDeAcceso(access);
    usuario.value = user;
    avisarCambioDeSesion();
    return user;
  }

  async function salir(): Promise<void> {
    await cerrarSesion();
    fijarTokenDeAcceso(null);
    usuario.value = null;
    avisarCambioDeSesion();
  }

  // Otra ventana entró o salió: esta ventana relee quién es la sesión
  // real y vuelve al inicio, en vez de seguir mostrando a otra persona.
  async function alCambiarLaSesionEnOtraVentana(): Promise<void> {
    if (!usuario.value) return;
    await restaurarSesion();
    window.location.assign("/");
  }

  async function confirmarMismaPersona(accesoNuevo: string): Promise<boolean> {
    const actual = usuario.value;
    if (!actual) return true;
    const { data } = await http.get<Usuario>("/auth/me/", {
      headers: { Authorization: `Bearer ${accesoNuevo}` },
    });
    if (data.public_id === actual.public_id) return true;
    usuario.value = data;
    window.location.assign("/");
    return false;
  }

  alRenovarElToken(confirmarMismaPersona);
  if (typeof window !== "undefined") {
    window.addEventListener("storage", (evento) => {
      if (evento.key === CLAVE_CAMBIO_DE_SESION) void alCambiarLaSesionEnOtraVentana();
    });
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
