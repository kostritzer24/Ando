<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";

import { AppButton, ErrorBanner, FormField } from "@/shared/components";

import { cambiarContrasena } from "../api/authApi";

const router = useRouter();

const contrasenaActual = ref("");
const contrasenaNueva = ref("");
const enviando = ref(false);
const mensajeError = ref("");

async function enviar(): Promise<void> {
  mensajeError.value = "";
  enviando.value = true;
  try {
    await cambiarContrasena(contrasenaActual.value, contrasenaNueva.value);
    await router.push("/");
  } catch {
    mensajeError.value =
      "No se pudo cambiar la contraseña. Revisá la contraseña actual y que la nueva cumpla los requisitos.";
  } finally {
    enviando.value = false;
  }
}
</script>

<template>
  <main class="change-password-page">
    <h1 class="change-password-page__titulo">Cambiá tu contraseña</h1>
    <p class="change-password-page__subtitulo">
      Es tu primer ingreso. Elegí una contraseña nueva antes de seguir.
    </p>

    <ErrorBanner v-if="mensajeError" :mensaje="mensajeError" />

    <form class="change-password-page__formulario" @submit.prevent="enviar">
      <FormField
        id="contrasena-actual"
        etiqueta="Contraseña temporal"
        tipo="password"
        v-model="contrasenaActual"
        autocomplete="current-password"
      />
      <FormField
        id="contrasena-nueva"
        etiqueta="Contraseña nueva"
        tipo="password"
        v-model="contrasenaNueva"
        pista="Al menos 10 caracteres, y que no sea una contraseña común."
        autocomplete="new-password"
      />
      <AppButton tipo="submit" :deshabilitado="enviando">
        {{ enviando ? "Guardando…" : "Guardar" }}
      </AppButton>
    </form>
  </main>
</template>

<style scoped>
.change-password-page {
  max-width: 24rem;
  margin: 0 auto;
  padding: 3rem 1.25rem;
  display: flex;
  flex-direction: column;
  gap: var(--espacio-xl);
}

.change-password-page__titulo {
  font-family: var(--fuente-titulo);
  font-weight: 800;
  font-size: 1.6rem;
  margin: 0;
}

.change-password-page__subtitulo {
  margin: 0;
  color: var(--color-tinta-suave);
}

.change-password-page__formulario {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-lg);
}
</style>
