<script setup lang="ts">
import { confirmacionPendiente } from "@/shared/composables/useConfirmar";

import AppButton from "./AppButton.vue";
import AppModal from "./AppModal.vue";

function responder(confirmado: boolean): void {
  confirmacionPendiente.value?.resolver(confirmado);
}
</script>

<template>
  <AppModal
    v-if="confirmacionPendiente"
    :titulo="confirmacionPendiente.titulo"
    class="confirm-host"
    @cerrar="responder(false)"
  >
    <p v-if="confirmacionPendiente.mensaje" class="confirm-host__mensaje">
      {{ confirmacionPendiente.mensaje }}
    </p>
    <!-- Cancelar va primero en el DOM para que sea lo que recibe el foco:
         un Enter distraído no debe dar de baja nada. -->
    <div class="confirm-host__acciones">
      <AppButton variante="secundario" @click="responder(false)">
        {{ confirmacionPendiente.etiquetaCancelar ?? "Cancelar" }}
      </AppButton>
      <AppButton :variante="confirmacionPendiente.peligro ? 'peligro' : 'primario'" @click="responder(true)">
        {{ confirmacionPendiente.etiquetaConfirmar ?? "Confirmar" }}
      </AppButton>
    </div>
  </AppModal>
</template>

<style scoped>
.confirm-host__mensaje {
  margin: 0;
  color: var(--color-tinta-suave);
}

.confirm-host__acciones {
  display: flex;
  flex-direction: column-reverse;
  gap: var(--espacio-sm);
}

@media (min-width: 40rem) {
  .confirm-host__acciones {
    flex-direction: row;
    justify-content: flex-end;
  }
}
</style>
