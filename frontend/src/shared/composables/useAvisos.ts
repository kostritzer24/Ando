import { ref } from "vue";

export interface Aviso {
  id: number;
  mensaje: string;
  tipo: "exito" | "error";
}

/** Los avisos visibles — los lee `AvisosHost`, montado en `App.vue`. */
export const avisos = ref<Aviso[]>([]);

const DURACION_MS = 4500;
let siguienteId = 1;

export function cerrarAviso(id: number): void {
  avisos.value = avisos.value.filter((aviso) => aviso.id !== id);
}

/** Confirma en voz baja que algo se guardó ("Sección dada de baja"), sin
 * interrumpir: aparece abajo, lo anuncia el lector de pantalla y se va
 * solo. Los errores que exigen una acción siguen yendo en `ErrorBanner`. */
export function avisar(mensaje: string, tipo: Aviso["tipo"] = "exito"): void {
  const id = siguienteId++;
  avisos.value = [...avisos.value.slice(-2), { id, mensaje, tipo }];
  setTimeout(() => cerrarAviso(id), DURACION_MS);
}
