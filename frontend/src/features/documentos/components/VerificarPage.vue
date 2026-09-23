<script setup lang="ts">
import { isAxiosError } from "axios";
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";

import { verificarDocumento } from "../api/documentosApi";
import type { DocumentoVerificado } from "../api/documentosApi";

const route = useRoute();
const cargando = ref(true);
const documento = ref<DocumentoVerificado | null>(null);
const noEncontrado = ref(false);

onMounted(async () => {
  try {
    documento.value = await verificarDocumento(String(route.params.codigo));
  } catch (error) {
    if (isAxiosError(error) && error.response?.status === 404) {
      noEncontrado.value = true;
    }
  } finally {
    cargando.value = false;
  }
});
</script>

<template>
  <main class="verificar-page">
    <h1>Verificación de documento</h1>

    <p v-if="cargando">Verificando…</p>
    <div v-else-if="documento" class="verificar-page__valido">
      <p class="verificar-page__titulo">Documento válido</p>
      <dl>
        <dt>Tipo</dt>
        <dd>{{ documento.tipo_documento }}</dd>
        <dt>Estudiante</dt>
        <dd>{{ documento.estudiante }}</dd>
        <dt>Fecha</dt>
        <dd>{{ documento.fecha }}</dd>
      </dl>
    </div>
    <div v-else class="verificar-page__invalido">
      <p class="verificar-page__titulo">Este código no corresponde a un documento válido.</p>
    </div>
  </main>
</template>

<style scoped>
.verificar-page {
  max-width: 28rem;
  margin: 0 auto;
  padding: 3rem 1.25rem;
}

.verificar-page h1 {
  font-family: var(--fuente-titulo);
  font-size: var(--texto-md);
  margin: 0 0 var(--espacio-xl);
}

.verificar-page__titulo {
  font-weight: 700;
  margin: 0 0 var(--espacio-md);
}

.verificar-page__valido {
  color: var(--color-etiqueta-taller-texto);
}

.verificar-page__valido dl {
  color: var(--color-tinta);
  font-weight: 400;
}

.verificar-page__valido dt {
  font-size: var(--texto-sm);
  color: var(--color-tinta-suave);
  margin-top: var(--espacio-sm);
}

.verificar-page__valido dd {
  margin: 0;
  font-weight: 600;
}

.verificar-page__invalido {
  color: var(--color-etiqueta-alerta-texto);
}
</style>
