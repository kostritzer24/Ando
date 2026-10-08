<script setup lang="ts">
import { isAxiosError } from "axios";
import { computed, reactive, ref } from "vue";

import { AppButton, ErrorBanner, FormField, PageHeader } from "@/shared/components";
import { avisar } from "@/shared/composables/useAvisos";

import { cambiarContrasena } from "../api/authApi";
import { useAuthStore } from "../stores/authStore";

const auth = useAuthStore();

const nombre = computed(
  () => [auth.usuario?.first_name, auth.usuario?.last_name].filter(Boolean).join(" ") || auth.usuario?.username,
);
const ultimoIngreso = computed(() =>
  auth.usuario?.last_login
    ? new Intl.DateTimeFormat("es-GT", { dateStyle: "long", timeStyle: "short" }).format(
        new Date(auth.usuario.last_login),
      )
    : "—",
);

// Nombre, correo y rol los administra Dirección o el Administrador del
// sistema (RF-01, sin registro libre): acá solo se consultan.
const datos = computed(() => [
  { etiqueta: "Nombre", valor: nombre.value },
  { etiqueta: "Usuario", valor: auth.usuario?.username },
  { etiqueta: "Rol", valor: auth.usuario?.role_name },
  { etiqueta: "Correo", valor: auth.usuario?.email || "Sin correo registrado" },
  { etiqueta: "Último ingreso", valor: ultimoIngreso.value },
]);

const formulario = reactive({ actual: "", nueva: "", confirmacion: "" });
const guardando = ref(false);
const error = ref("");
const errorConfirmacion = computed(() =>
  formulario.confirmacion && formulario.confirmacion !== formulario.nueva ? "No coincide con la contraseña nueva." : "",
);

async function guardar(): Promise<void> {
  if (formulario.nueva !== formulario.confirmacion) return;
  guardando.value = true;
  error.value = "";
  try {
    await cambiarContrasena(formulario.actual, formulario.nueva);
    Object.assign(formulario, { actual: "", nueva: "", confirmacion: "" });
    avisar("Contraseña cambiada. La próxima vez entra con la nueva.");
  } catch (e) {
    const datosError = isAxiosError(e) ? (e.response?.data as Record<string, unknown> | undefined) : undefined;
    const detalle = datosError?.contrasena_nueva ?? datosError?.detail;
    error.value = Array.isArray(detalle)
      ? String(detalle[0])
      : typeof detalle === "string"
        ? detalle
        : "No se pudo cambiar la contraseña. Inténtalo de nuevo.";
  } finally {
    guardando.value = false;
  }
}
</script>

<template>
  <section class="cuenta-page">
    <PageHeader titulo="Mi cuenta" />

    <div class="cuenta-page__bloques">
      <section class="cuenta-page__bloque" aria-labelledby="titulo-datos">
        <h2 id="titulo-datos" class="cuenta-page__subtitulo">Tus datos</h2>
        <dl class="cuenta-page__datos">
          <div v-for="dato in datos" :key="dato.etiqueta" class="cuenta-page__dato">
            <dt>{{ dato.etiqueta }}</dt>
            <dd>{{ dato.valor }}</dd>
          </div>
        </dl>
        <p class="cuenta-page__nota">Si algún dato está mal, pedile a Dirección que lo corrija.</p>
      </section>

      <section class="cuenta-page__bloque" aria-labelledby="titulo-contrasena">
        <h2 id="titulo-contrasena" class="cuenta-page__subtitulo">Cambiar contraseña</h2>
        <form class="cuenta-page__formulario" @submit.prevent="guardar">
          <ErrorBanner v-if="error" :mensaje="error" />
          <FormField
            id="contrasena-actual"
            etiqueta="Contraseña actual"
            tipo="password"
            v-model="formulario.actual"
            autocomplete="current-password"
            required
          />
          <FormField
            id="contrasena-nueva"
            etiqueta="Contraseña nueva"
            tipo="password"
            v-model="formulario.nueva"
            pista="Al menos 10 caracteres, y que no sea una contraseña común."
            autocomplete="new-password"
            required
          />
          <FormField
            id="contrasena-confirmacion"
            etiqueta="Repite la contraseña nueva"
            tipo="password"
            v-model="formulario.confirmacion"
            :mensaje-error="errorConfirmacion"
            autocomplete="new-password"
            required
          />
          <AppButton tipo="submit" :deshabilitado="guardando || Boolean(errorConfirmacion)">
            {{ guardando ? "Guardando…" : "Cambiar contraseña" }}
          </AppButton>
        </form>
      </section>
    </div>
  </section>
</template>

<style scoped>
.cuenta-page__bloques {
  display: grid;
  gap: var(--espacio-lg);
  align-items: start;
}

.cuenta-page__bloque {
  padding: var(--espacio-xl) var(--espacio-lg);
  background: var(--color-papel);
  border: 1px solid var(--color-linea);
  border-radius: var(--radio-lg);
}

.cuenta-page__subtitulo {
  font-size: var(--texto-md);
  margin-bottom: var(--espacio-lg);
}

.cuenta-page__datos {
  margin: 0;
}

.cuenta-page__dato {
  display: grid;
  grid-template-columns: 8rem minmax(0, 1fr);
  gap: var(--espacio-md);
  padding: var(--espacio-sm) 0;
  border-bottom: 1px solid var(--color-linea);
}

.cuenta-page__dato:last-child {
  border-bottom: none;
}

.cuenta-page__dato dt {
  font-size: var(--texto-sm);
  color: var(--color-tinta-suave);
}

.cuenta-page__dato dd {
  margin: 0;
  overflow-wrap: anywhere;
}

.cuenta-page__nota {
  margin: var(--espacio-md) 0 0;
  font-size: var(--texto-sm);
  color: var(--color-tinta-suave);
}

.cuenta-page__formulario {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-lg);
}

@media (min-width: 40rem) {
  .cuenta-page__bloque {
    padding: var(--espacio-2xl);
  }
}

@media (min-width: 64rem) {
  .cuenta-page__bloques {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: var(--espacio-2xl);
  }
}
</style>
