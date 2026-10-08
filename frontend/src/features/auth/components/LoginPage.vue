<script setup lang="ts">
import { isAxiosError } from "axios";
import { ref } from "vue";
import { useRouter } from "vue-router";

import { DESTINO_POR_ROL } from "@/app/router";
import { AppButton, ErrorBanner, FormField } from "@/shared/components";

import { useAuthStore } from "../stores/authStore";
import PantallaAcceso from "./PantallaAcceso.vue";

const auth = useAuthStore();
const router = useRouter();

const username = ref("");
const password = ref("");
const enviando = ref(false);
const mensajeError = ref("");

// Antes todo error decía "Usuario o contraseña incorrectos": una familia
// bloqueada temporalmente (RN-16) o alguien que chocó con el límite de
// intentos (RNF-05) creía que se había equivocado de contraseña y volvía a
// intentar, alargando el bloqueo.
function mensajeDeError(error: unknown): string {
  if (!isAxiosError(error) || !error.response) {
    return "No se pudo conectar con el sistema. Revisa tu conexión e inténtalo de nuevo.";
  }
  if (error.response.status === 429) {
    return "Demasiados intentos seguidos. Espera un minuto y vuelve a intentarlo.";
  }
  const detalle = (error.response.data as { detail?: unknown } | undefined)?.detail;
  if (typeof detalle === "string" && detalle.includes("bloqueada")) {
    return detalle;
  }
  return "Usuario o contraseña incorrectos. Vuelve a intentarlo.";
}

async function enviar(): Promise<void> {
  mensajeError.value = "";
  enviando.value = true;
  try {
    const usuario = await auth.ingresar(username.value, password.value);
    if (usuario.must_change_password) {
      await router.push("/cambiar-contrasena");
      return;
    }
    await router.push(DESTINO_POR_ROL[usuario.role_name] ?? "/");
  } catch (error) {
    mensajeError.value = mensajeDeError(error);
  } finally {
    enviando.value = false;
  }
}
</script>

<template>
  <PantallaAcceso titulo="Ingresar" subtitulo="Entra con el usuario y la contraseña que te dio el centro.">
    <ErrorBanner v-if="mensajeError" :mensaje="mensajeError" />

    <form class="login-page__formulario" @submit.prevent="enviar">
      <FormField id="username" etiqueta="Usuario" v-model="username" autocomplete="username" autocapitalize="none" spellcheck="false" />
      <FormField
        id="password"
        etiqueta="Contraseña"
        tipo="password"
        v-model="password"
        autocomplete="current-password"
      />
      <AppButton tipo="submit" bloque :deshabilitado="enviando">
        {{ enviando ? "Entrando…" : "Entrar" }}
      </AppButton>
    </form>
  </PantallaAcceso>
</template>

<style scoped>
.login-page__formulario {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-lg);
}
</style>
