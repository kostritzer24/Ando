<script setup lang="ts">
import { useAuthStore } from "@/features/auth/stores/authStore";

const auth = useAuthStore();
</script>

<template>
  <main class="pagina-inicio">
    <h1>Portal de familias</h1>
    <p>Hola, {{ auth.usuario?.first_name || auth.usuario?.username }}.</p>
    <p class="pagina-inicio__nota">
      El calendario semanal, notas, asistencia, pagos y boletín se agregan a
      partir de la Fase 10, cuando ya exista el expediente del estudiante.
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
