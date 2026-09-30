import { http } from "@/app/http";
import { crearRecursoCrud, obtenerTodas } from "@/shared/api/resource";
import type { AccessLog, AuditLog, Paginada, Role, Usuario } from "@/shared/types/models";

export const usuariosApi = crearRecursoCrud<Usuario>("/users/");

export async function listarRoles(): Promise<Role[]> {
  return (await obtenerTodas<Role>("/roles/")).results;
}

export async function crearUsuario(payload: {
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  role: string;
  contrasena_temporal: string;
}): Promise<Usuario> {
  const { data } = await http.post<Usuario>("/users/", payload);
  return data;
}

export async function restablecerContrasena(publicId: string, contrasenaTemporal: string): Promise<void> {
  await http.post(`/users/${publicId}/reset-password/`, { contrasena_temporal: contrasenaTemporal });
}

// La bitácora y el registro de acceso crecen sin límite (este último guarda
// cada pantalla consultada): acá sí se pagina contra el servidor en vez de
// traer todo con `obtenerTodas`.
export const TAMANO_PAGINA_BITACORA = 50;

export async function listarBitacora(pagina: number): Promise<Paginada<AuditLog>> {
  const { data } = await http.get<Paginada<AuditLog>>("/audit-log/", {
    params: { page: pagina, page_size: TAMANO_PAGINA_BITACORA },
  });
  return data;
}

export async function listarAccesos(pagina: number, usuario?: string): Promise<Paginada<AccessLog>> {
  const { data } = await http.get<Paginada<AccessLog>>("/access-log/", {
    params: { page: pagina, page_size: TAMANO_PAGINA_BITACORA, user: usuario || undefined },
  });
  return data;
}
