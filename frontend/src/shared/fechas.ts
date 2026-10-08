/** Fecha local como `AAAA-MM-DD`. `toISOString()` devuelve la fecha en UTC, y
 * en Guatemala (UTC-6) a partir de las 6 pm ya es el día siguiente. */
export function aFechaIso(fecha: Date): string {
  const mes = String(fecha.getMonth() + 1).padStart(2, "0");
  const dia = String(fecha.getDate()).padStart(2, "0");
  return `${fecha.getFullYear()}-${mes}-${dia}`;
}

export function hoyIso(): string {
  return aFechaIso(new Date());
}

/** Hoy si es de lunes a viernes; si es fin de semana, el viernes anterior
 * (el centro no abre sábados ni domingos). */
export function ultimoDiaHabilIso(desde: Date = new Date()): string {
  const fecha = new Date(desde);
  const dia = fecha.getDay(); // 0 domingo … 6 sábado
  if (dia === 6) fecha.setDate(fecha.getDate() - 1);
  if (dia === 0) fecha.setDate(fecha.getDate() - 2);
  return aFechaIso(fecha);
}

const FECHA_ISO = /^(\d{4})-(\d{2})-(\d{2})$/;

/** `2015-01-01` → `01/01/2015`. Cualquier otro valor se devuelve igual. */
export function fechaLegible<T>(valor: T): T | string {
  if (typeof valor !== "string") return valor;
  const partes = FECHA_ISO.exec(valor);
  return partes ? `${partes[3]}/${partes[2]}/${partes[1]}` : valor;
}
