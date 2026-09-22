import { http } from "@/app/http";
import { crearRecursoCrud } from "@/shared/api/resource";
import type { Paginada, TeacherAssignment, Usuario } from "@/shared/types/models";

export const assignmentsApi = crearRecursoCrud<TeacherAssignment>("/assignments/");

export async function listarUsuariosPorRoles(roles: string[]): Promise<Usuario[]> {
  const { data } = await http.get<Paginada<Usuario>>("/users/");
  return data.results.filter((usuario) => roles.includes(usuario.role_name));
}
