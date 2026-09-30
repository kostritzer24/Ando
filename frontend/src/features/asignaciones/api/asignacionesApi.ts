import { crearRecursoCrud, obtenerTodas } from "@/shared/api/resource";
import type { TeacherAssignment, Usuario } from "@/shared/types/models";

export const assignmentsApi = crearRecursoCrud<TeacherAssignment>("/assignments/");

export async function listarUsuariosPorRoles(roles: string[]): Promise<Usuario[]> {
  const data = await obtenerTodas<Usuario>("/users/");
  return data.results.filter((usuario) => roles.includes(usuario.role_name));
}
