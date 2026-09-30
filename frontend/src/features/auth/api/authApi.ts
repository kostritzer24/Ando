import { http } from "@/app/http";
import type { Permisos } from "@/shared/permisos";
import type { components } from "@/shared/types/api";

/** La persona en sesión con los permisos de su rol por área (`/auth/me/`
 * y `/auth/login/`). El esquema los declara como JSON sin forma, así que
 * se tipan acá. */
export type Usuario = Omit<components["schemas"]["Me"], "permissions"> & { permissions: Permisos };

interface RespuestaLogin {
  access: string;
  user: Usuario;
}

export async function iniciarSesion(username: string, password: string): Promise<RespuestaLogin> {
  const { data } = await http.post<RespuestaLogin>("/auth/login/", { username, password });
  return data;
}

export async function refrescarToken(): Promise<string> {
  const { data } = await http.post<{ access: string }>("/auth/refresh/");
  return data.access;
}

export async function obtenerPerfil(): Promise<Usuario> {
  const { data } = await http.get<Usuario>("/auth/me/");
  return data;
}

export async function cerrarSesion(): Promise<void> {
  await http.post("/auth/logout/");
}

export async function cambiarContrasena(
  contrasenaActual: string,
  contrasenaNueva: string,
): Promise<void> {
  await http.post("/auth/change-password/", {
    contrasena_actual: contrasenaActual,
    contrasena_nueva: contrasenaNueva,
  });
}
