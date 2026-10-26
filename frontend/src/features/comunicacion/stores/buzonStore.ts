import { defineStore } from "pinia";
import { computed, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { usePermisos } from "@/shared/permisos";

import { contarNoLeidas } from "../api/comunicacionApi";

// RN-19: el contador de conversaciones sin leer va en el menú y en la
// pantalla del buzón a la vez; vive aquí para que abrir una conversación
// lo actualice en ambos lados sin recargar la página.
export const useBuzonStore = defineStore("buzon", () => {
  const noLeidas = ref(0);

  async function actualizar(): Promise<void> {
    try {
      noLeidas.value = await contarNoLeidas();
    } catch {
      // El contador es una ayuda: si falla, el buzón sigue funcionando.
    }
  }

  return { noLeidas, actualizar };
});

/** Insignia del buzón para el menú de un layout: se pide al entrar y cada
 * vez que cambia la pantalla (no hay tiempo real, HU-25). Solo para los
 * roles con acceso al buzón; para los demás la consulta daría 403. */
export function useInsigniaBuzon(rutaBuzon: string) {
  const buzon = useBuzonStore();
  const { puedeVer } = usePermisos();
  const route = useRoute();

  function refrescar(): void {
    if (puedeVer("buzon")) void buzon.actualizar();
  }

  onMounted(refrescar);
  watch(() => route.path, refrescar);

  return computed(() => ({ [rutaBuzon]: buzon.noLeidas }));
}
