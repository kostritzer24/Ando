<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";

import { mensajeDelServidor } from "@/shared/api/errores";
import { AppButton, ErrorBanner, FormField } from "@/shared/components";

import { cambiarContrasena } from "../api/authApi";
import PantallaAcceso from "./PantallaAcceso.vue";

const router = useRouter();

const contrasenaNueva = ref("");
const repeticion = ref("");
const enviando = ref(false);
const mensajeError = ref("");

async function enviar(): Promise<void> {
  mensajeError.value = "";
  if (contrasenaNueva.value !== repeticion.value) {
    mensajeError.value = "Las dos contraseñas no coinciden. Escríbelas de nuevo.";
    return;
  }
  enviando.value = true;
  try {
    await cambiarContrasena(null, contrasenaNueva.value);
    await router.push("/");
  } catch (error) {
    mensajeError.value = mensajeDelServidor(
      error,
      "No se pudo cambiar la contraseña. Revisa la contraseña actual y que la nueva cumpla los requisitos.",
    );
  } finally {
    enviando.value = false;
  }
}
</script>

<template>
  <PantallaAcceso
    titulo="Cambia tu contraseña"
    subtitulo="Es tu primer ingreso. Elige una contraseña nueva antes de seguir."
  >
    <ErrorBanner v-if="mensajeError" :mensaje="mensajeError" />

    <form class="change-password-page__formulario" @submit.prevent="enviar">
      <FormField
        id="contrasena-nueva"
        etiqueta="Contraseña nueva"
        tipo="password"
        v-model="contrasenaNueva"
        pista="Al menos 10 caracteres, y que no sea una contraseña común."
        autocomplete="new-password"
      />
      <FormField
        id="contrasena-repeticion"
        etiqueta="Repite la contraseña nueva"
        tipo="password"
        v-model="repeticion"
        autocomplete="new-password"
      />
      <AppButton tipo="submit" bloque :deshabilitado="enviando">
        {{ enviando ? "Guardando…" : "Guardar" }}
      </AppButton>
    </form>
  </PantallaAcceso>
</template>

<style scoped>
.change-password-page__formulario {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-lg);
}
</style>
