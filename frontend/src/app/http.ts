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
  _intentosTransitorios?: number;
}

// En Render (plan gratuito) y Neon el servidor "duerme" tras un rato sin
// uso: la primera lectura llega sin respuesta o con 502/503/504 y la misma
// petición funciona segundos después (antes se arreglaba recargando la
// página). Las lecturas se reintentan solas; las escrituras nunca, para no
// duplicar nada.
const MAX_REINTENTOS_TRANSITORIOS = 3;
const ESTADOS_TRANSITORIOS = new Set([502, 503, 504]);

function esFalloTransitorio(error: { response?: { status: number }; code?: string }): boolean {
  if (!error.response) return error.code !== "ERR_CANCELED";
  return ESTADOS_TRANSITORIOS.has(error.response.status);
}

const esperar = (ms: number): Promise<void> => new Promise((resolver) => setTimeout(resolver, ms));

let refrescoEnCurso: Promise<string> | null = null;

// La cookie de refresco es una sola por navegador: si en otra ventana se
// entra con otro usuario, esa cookie cambia de dueño y la renovación del
// token de ESTA ventana la convertiría, sin avisar, en el otro usuario
// (de ahí los 403 «sin permiso» que se arreglaban recargando). Tras
// renovar se confirma que la persona sigue siendo la misma; si no, el
// store reconstruye la sesión y la pantalla vuelve al inicio.
type AlRenovarSesion = (accesoNuevo: string) => Promise<boolean>;
let alRenovarSesion: AlRenovarSesion | null = null;

export function alRenovarElToken(manejador: AlRenovarSesion): void {
  alRenovarSesion = manejador;
}

http.interceptors.response.use(
  (respuesta) => respuesta,
  async (error) => {
    const peticionOriginal = error.config as PeticionReintentable | undefined;
    if (
      peticionOriginal &&
      peticionOriginal.method?.toLowerCase() === "get" &&
      esFalloTransitorio(error) &&
      (peticionOriginal._intentosTransitorios ?? 0) < MAX_REINTENTOS_TRANSITORIOS
    ) {
      const intento = (peticionOriginal._intentosTransitorios ?? 0) + 1;
      peticionOriginal._intentosTransitorios = intento;
      await esperar(1000 * intento);
      return http(peticionOriginal);
    }
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
          .then(async (respuesta) => {
            fijarTokenDeAcceso(respuesta.data.access);
            if (alRenovarSesion && !(await alRenovarSesion(respuesta.data.access))) {
              throw new Error("La sesión cambió en otra ventana.");
            }
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
