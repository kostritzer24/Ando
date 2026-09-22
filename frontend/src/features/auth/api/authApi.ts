import { http } from "@/app/http";

export interface Usuario {
  public_id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  role_name: string;
  is_active: boolean;
  must_change_password: boolean;
}

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
