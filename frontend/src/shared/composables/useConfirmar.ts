import { shallowRef } from "vue";

export interface OpcionesConfirmacion {
  titulo: string;
  mensaje?: string;
  etiquetaConfirmar?: string;
  etiquetaCancelar?: string;
  /** Pinta el botón de confirmar en rojo: dar de baja, eliminar, quitar. */
  peligro?: boolean;
}

interface ConfirmacionPendiente extends OpcionesConfirmacion {
  resolver: (confirmado: boolean) => void;
}

/** La confirmación que está esperando respuesta — la lee `ConfirmHost`,
 * montado una sola vez en `App.vue`. */
export const confirmacionPendiente = shallowRef<ConfirmacionPendiente | null>(null);

/** Reemplaza al `window.confirm()` nativo (sección 15.2: "lo destructivo se
 * confirma"), con la estética del sistema, texto propio en los botones y
 * foco accesible.
 *
 *   if (!(await confirmar({ titulo: "¿Dar de baja esta sección?", peligro: true }))) return;
 */
export function confirmar(opciones: OpcionesConfirmacion): Promise<boolean> {
  confirmacionPendiente.value?.resolver(false);
  return new Promise((resolve) => {
    confirmacionPendiente.value = {
      ...opciones,
      resolver: (confirmado) => {
        confirmacionPendiente.value = null;
        resolve(confirmado);
      },
    };
  });
}
