<script setup lang="ts">
import { useAuthStore } from "@/features/auth/stores/authStore";

const auth = useAuthStore();
</script>

<template>
  <main class="pagina-inicio">
    <h1>Portal operativo</h1>
    <p>Hola, {{ auth.usuario?.first_name || auth.usuario?.username }}.</p>
    <p class="pagina-inicio__nota">
      Asistencia ya está disponible en el menú de la izquierda. Notas, horarios y
      calendario se van agregando en las próximas fases.
    </p>
  </main>
</template>

<style scoped>
.pagina-inicio {
  max-width: 40rem;
  margin: 0 auto;
  padding: 2rem 1.25rem;
}

.pagina-inicio__nota {
  color: var(--color-tinta-suave);
}
</style>
