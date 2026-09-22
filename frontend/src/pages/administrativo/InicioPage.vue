<script setup lang="ts">
import { useAuthStore } from "@/features/auth/stores/authStore";

const auth = useAuthStore();
</script>

<template>
  <main class="pagina-inicio">
    <h1>Portal administrativo</h1>
    <p>Hola, {{ auth.usuario?.first_name || auth.usuario?.username }}.</p>
    <p class="pagina-inicio__nota">
      Los datos maestros, estudiantes, encargados y asignaciones ya están
      disponibles en el menú de la izquierda. El resto de los módulos
      (horarios, notas, pagos, documentos, avisos y reportes) se van
      agregando en las próximas fases.
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
