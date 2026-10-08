import axios from "axios";

/**
 * Para datos auxiliares de una pantalla (listas para mostrar nombres o llenar
 * un selector) que pueden estar fuera del alcance del rol: si el servidor
 * responde 403 se usa `vacio` y la pantalla sigue funcionando, en vez de
 * mostrar un error de carga completo. Cualquier otro error se propaga.
 */
export async function opcional<T>(peticion: Promise<T>, vacio: T): Promise<T> {
  try {
    return await peticion;
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.status === 403) {
      return vacio;
    }
    throw error;
  }
}
