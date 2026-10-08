import { isAxiosError } from "axios";

const ETIQUETAS_DE_CAMPO: Record<string, string> = {
  first_name: "Nombres",
  last_name: "Apellidos",
  birth_date: "Fecha de nacimiento",
  address: "Dirección",
  username: "Usuario",
  email: "Correo",
  name: "Nombre",
  year: "Año",
  start_date: "Fecha de inicio",
  end_date: "Fecha de fin",
  event_date: "Fecha",
  start_time: "Hora de inicio",
  end_time: "Hora de fin",
  title: "Título",
  section: "Sección",
  course: "Curso",
  teacher: "Docente",
  grade: "Grado",
  letter: "Letra",
  number: "Número",
  reason_detail: "Detalle",
  justification_type: "Tipo de justificación",
};

function primerMensaje(valor: unknown): string {
  let actual: unknown = valor;
  while (actual && typeof actual === "object") {
    actual = Array.isArray(actual) ? actual[0] : Object.values(actual)[0];
  }
  return typeof actual === "string" ? actual : "";
}

/**
 * El motivo concreto que devolvió el servidor en un 400 (campo faltante,
 * fecha inválida, dato repetido…), con el nombre del campo cuando se
 * conoce, para mostrarlo dentro del formulario. Si no hay un mensaje
 * legible, `porDefecto`.
 */
export function mensajeDelServidor(error: unknown, porDefecto: string): string {
  if (!isAxiosError(error) || error.response?.status !== 400) return porDefecto;
  const cuerpo: unknown = error.response.data;
  if (cuerpo && typeof cuerpo === "object" && !Array.isArray(cuerpo)) {
    const [campo, valor] = Object.entries(cuerpo)[0] ?? [];
    const mensaje = primerMensaje(valor);
    if (!mensaje) return porDefecto;
    const etiqueta = campo ? ETIQUETAS_DE_CAMPO[campo] : undefined;
    return etiqueta ? `${etiqueta}: ${mensaje}` : mensaje;
  }
  return primerMensaje(cuerpo) || porDefecto;
}
