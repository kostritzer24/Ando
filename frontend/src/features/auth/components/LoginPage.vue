<script setup lang="ts">
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
  } catch {
    mensajeError.value = "Usuario o contraseña incorrectos. Volvé a intentar.";
  } finally {
    enviando.value = false;
  }
}
</script>

<template>
  <PantallaAcceso titulo="Ingresar" subtitulo="Entrá con el usuario y la contraseña que te dio el centro.">
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
