<script setup lang="ts">
// Fila con línea inferior, nunca una tarjeta con sombra (sección 15.4 del
// prompt maestro) — misma idea que `ListRow`, adaptada a tabla densa para
// los portales de escritorio (administrativo/operativo).
defineProps<{
  columnas: { clave: string; etiqueta: string }[];
  filas: Record<string, unknown>[];
}>();
</script>

<template>
  <table class="data-table">
    <thead>
      <tr>
        <th v-for="columna in columnas" :key="columna.clave">{{ columna.etiqueta }}</th>
        <th v-if="$slots.acciones" class="data-table__col-acciones">Acciones</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="(fila, indice) in filas" :key="indice">
        <td v-for="columna in columnas" :key="columna.clave">
          <slot :name="`celda-${columna.clave}`" :fila="fila">
            {{ fila[columna.clave] }}
          </slot>
        </td>
        <td v-if="$slots.acciones" class="data-table__col-acciones">
          <slot name="acciones" :fila="fila" />
        </td>
      </tr>
    </tbody>
  </table>
</template>

<style scoped>
.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--texto-base);
}

.data-table th {
  text-align: left;
  font-weight: 600;
  font-size: var(--texto-sm);
  color: var(--color-tinta-suave);
  padding: var(--espacio-sm) var(--espacio-md);
  border-bottom: 1px solid var(--color-linea);
}

.data-table td {
  padding: var(--espacio-sm) var(--espacio-md);
  border-bottom: 1px solid var(--color-linea);
  vertical-align: middle;
}

.data-table__col-acciones {
  text-align: right;
  white-space: nowrap;
}
</style>
