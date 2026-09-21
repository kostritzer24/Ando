<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";

import { DESTINO_POR_ROL } from "@/app/router";
import { AppButton, ErrorBanner, FormField } from "@/shared/components";

import { useAuthStore } from "../stores/authStore";

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
  <main class="login-page">
    <h1 class="login-page__titulo">Ingresar</h1>
    <p class="login-page__subtitulo">Entrá con el usuario y la contraseña que te dio el centro.</p>

    <ErrorBanner v-if="mensajeError" :mensaje="mensajeError" class="login-page__error" />

    <form class="login-page__formulario" @submit.prevent="enviar">
      <FormField
        id="username"
        etiqueta="Usuario"
        v-model="username"
        autocomplete="username"
      />
      <FormField
        id="password"
        etiqueta="Contraseña"
        tipo="password"
        v-model="password"
        autocomplete="current-password"
      />
      <AppButton tipo="submit" :deshabilitado="enviando">
        {{ enviando ? "Entrando…" : "Entrar" }}
      </AppButton>
    </form>
  </main>
</template>

<style scoped>
.login-page {
  max-width: 24rem;
  margin: 0 auto;
  padding: 3rem 1.25rem;
  display: flex;
  flex-direction: column;
  gap: var(--espacio-xl);
}

.login-page__titulo {
  font-family: var(--fuente-titulo);
  font-weight: 800;
  font-size: 1.6rem;
  margin: 0;
}

.login-page__subtitulo {
  margin: 0;
  color: var(--color-tinta-suave);
}

.login-page__formulario {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-lg);
}
</style>
