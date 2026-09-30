// Palabras cortas, sin tildes ni letras que se confunden al dictarlas
// (la contraseña temporal se entrega en persona o por teléfono, sección
// 14.1: nada de correo automático).
const PALABRAS = [
  "arbol", "barco", "campo", "cielo", "fuego", "gato", "huerto", "lago", "luna", "mango",
  "mar", "monte", "nube", "palma", "patio", "piedra", "puente", "rio", "sol", "trigo",
  "vela", "verde", "volcan", "zorro",
];

function alAzar(maximo: number): number {
  const valores = new Uint32Array(1);
  crypto.getRandomValues(valores);
  return valores[0] % maximo;
}

function capitalizar(palabra: string): string {
  return palabra.charAt(0).toUpperCase() + palabra.slice(1);
}

/** Contraseña temporal fácil de dictar y que pasa los validadores de
 * Django (al menos 10 caracteres, no común, no solo números): dos
 * palabras y cuatro dígitos, "Luna-Barco-4827". La persona la cambia en
 * su primer ingreso de todos modos. */
export function generarContrasenaTemporal(): string {
  const primera = capitalizar(PALABRAS[alAzar(PALABRAS.length)]);
  const segunda = capitalizar(PALABRAS[alAzar(PALABRAS.length)]);
  const numero = String(alAzar(9000) + 1000);
  return `${primera}-${segunda}-${numero}`;
}
