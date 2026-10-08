import { http } from "@/app/http";
import { crearRecursoCrud, obtenerTodas } from "@/shared/api/resource";
import type {
  Enrollment,
  Guardian,
  GuardianStudentLinkRead,
  Role,
  Student,
  StudentSensitive,
  Usuario,
} from "@/shared/types/models";

export const studentsApi = crearRecursoCrud<Student>("/students/");
export const guardiansApi = crearRecursoCrud<Guardian>("/guardians/");
export const enrollmentsApi = crearRecursoCrud<Enrollment>("/enrollments/");

export async function obtenerDatosSensibles(studentPublicId: string): Promise<StudentSensitive> {
  const { data } = await http.get<StudentSensitive>(`/students/${studentPublicId}/sensitive/`);
  return data;
}

export async function actualizarDatosSensibles(
  studentPublicId: string,
  payload: Partial<StudentSensitive>,
): Promise<StudentSensitive> {
  const { data } = await http.patch<StudentSensitive>(
    `/students/${studentPublicId}/sensitive/`,
    payload,
  );
  return data;
}

export async function listarVinculos(guardianPublicId: string): Promise<GuardianStudentLinkRead[]> {
  const { data } = await http.get<GuardianStudentLinkRead[]>(
    `/guardians/${guardianPublicId}/link-student/`,
  );
  return data;
}

export async function vincularEstudiante(
  guardianPublicId: string,
  payload: { student: string; relationship: string; is_primary?: boolean },
): Promise<void> {
  await http.post(`/guardians/${guardianPublicId}/link-student/`, payload);
}

export async function desvincularEstudiante(
  guardianPublicId: string,
  studentPublicId: string,
): Promise<void> {
  await http.delete(`/guardians/${guardianPublicId}/link-student/${studentPublicId}/`);
}

// Un encargado necesita una cuenta de usuario antes de poder crearse
// (Guardian.user es obligatorio): esta pantalla arma las dos cosas en un
// solo paso, primero el usuario con rol "Padre de familia" y después el
// perfil de encargado. Por eso la pantalla de Usuarios no ofrece ese rol
// al crear una cuenta: saldría suelta, sin encargado ni estudiante.
export async function crearUsuarioFamilia(payload: {
  username: string;
  contrasena_temporal: string;
  first_name?: string;
  last_name?: string;
  email?: string;
}): Promise<Usuario> {
  const rol = await obtenerRolPorNombre("Padre de familia");
  if (!rol) {
    throw new Error('No existe el rol "Padre de familia" — revisa la siembra de roles.');
  }
  const { data } = await http.post<Usuario>("/users/", { ...payload, role: rol.public_id });
  return data;
}

async function obtenerRolPorNombre(nombre: string): Promise<Role | undefined> {
  const data = await obtenerTodas<Role>("/roles/");
  return data.results.find((rol) => rol.name === nombre);
}
