import axios, { type InternalAxiosRequestConfig } from "axios";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

export const http = axios.create({
  baseURL: apiBaseUrl,
  // La cookie HttpOnly del token de refresco viaja sola con cada petición
  // (sección 14.1 del prompt maestro) — nunca se lee ni se guarda desde JS.
  withCredentials: true,
});

let tokenDeAcceso: string | null = null;

export function fijarTokenDeAcceso(token: string | null): void {
  tokenDeAcceso = token;
}

http.interceptors.request.use((config) => {
  if (tokenDeAcceso) {
    config.headers.Authorization = `Bearer ${tokenDeAcceso}`;
  }
  return config;
});

interface PeticionReintentable extends InternalAxiosRequestConfig {
  _reintentada?: boolean;
}

let refrescoEnCurso: Promise<string> | null = null;

http.interceptors.response.use(
  (respuesta) => respuesta,
  async (error) => {
    const peticionOriginal = error.config as PeticionReintentable | undefined;
    // Un 401 del login no es un token vencido: son credenciales malas o una
    // cuenta bloqueada, y la pantalla necesita ese mensaje, no el del
    // intento de renovación que lo reemplazaba.
    const esRutaDeSesion = peticionOriginal?.url === "/auth/refresh/" || peticionOriginal?.url === "/auth/login/";
    const noHayComoReintentar = !peticionOriginal || peticionOriginal._reintentada || esRutaDeSesion;

    if (error.response?.status !== 401 || noHayComoReintentar) {
      return Promise.reject(error);
    }

    peticionOriginal._reintentada = true;
    try {
      if (!refrescoEnCurso) {
        refrescoEnCurso = http
          .post<{ access: string }>("/auth/refresh/")
          .then((respuesta) => {
            fijarTokenDeAcceso(respuesta.data.access);
            return respuesta.data.access;
          })
          .finally(() => {
            refrescoEnCurso = null;
          });
      }
      const nuevoToken = await refrescoEnCurso;
      peticionOriginal.headers.Authorization = `Bearer ${nuevoToken}`;
      return http(peticionOriginal);
    } catch (errorDeRefresco) {
      fijarTokenDeAcceso(null);
      return Promise.reject(errorDeRefresco);
    }
  },
);
