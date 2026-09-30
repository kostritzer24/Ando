<script setup lang="ts" generic="F extends object">
import { ArrowDown, ArrowUp, ChevronLeft, ChevronRight, Search } from "lucide-vue-next";
import { computed, ref, useId, watch } from "vue";

export interface ColumnaTabla<T = Record<string, unknown>> {
  clave: string;
  etiqueta: string;
  /** Texto con el que se busca y se ordena esa columna, cuando la celda
   * muestra algo distinto del valor crudo (un nombre en vez de un id). */
  texto?: (fila: T) => string;
  ordenable?: boolean;
}

const props = withDefaults(
  defineProps<{
    columnas: ColumnaTabla<F>[];
    filas: F[];
    /** Muestra el buscador arriba de la tabla. */
    buscable?: boolean;
    placeholderBusqueda?: string;
    /** Filas por página; 0 desactiva la paginación. */
    porPagina?: number;
    /** Propiedad que identifica a cada fila (por omisión, `public_id`). */
    claveFila?: string;
    /** Nombre accesible de la tabla, para lectores de pantalla. */
    descripcion?: string;
  }>(),
  {
    buscable: false,
    placeholderBusqueda: "Buscar",
    porPagina: 25,
    claveFila: "public_id",
    descripcion: undefined,
  },
);

const idBuscador = useId();
const busqueda = ref("");
const orden = ref<{ clave: string; ascendente: boolean } | null>(null);
const pagina = ref(1);

function campo(fila: F, clave: string): unknown {
  return (fila as Record<string, unknown>)[clave];
}

function textoDe(fila: F, columna: ColumnaTabla<F>): string {
  if (columna.texto) return columna.texto(fila);
  const valor = campo(fila, columna.clave);
  return valor === null || valor === undefined ? "" : String(valor);
}

/** Sin mayúsculas ni tildes: "Pérez" se encuentra escribiendo "perez". */
function normalizar(texto: string): string {
  return texto.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
}

const filasFiltradas = computed(() => {
  const termino = normalizar(busqueda.value.trim());
  if (!termino) return props.filas;
  return props.filas.filter((fila) =>
    props.columnas.some((columna) => normalizar(textoDe(fila, columna)).includes(termino)),
  );
});

const filasOrdenadas = computed(() => {
  if (!orden.value) return filasFiltradas.value;
  const columna = props.columnas.find((c) => c.clave === orden.value?.clave);
  if (!columna) return filasFiltradas.value;
  const signo = orden.value.ascendente ? 1 : -1;
  return [...filasFiltradas.value].sort(
    (a, b) => signo * textoDe(a, columna).localeCompare(textoDe(b, columna), "es", { numeric: true }),
  );
});

const totalPaginas = computed(() =>
  props.porPagina > 0 ? Math.max(1, Math.ceil(filasOrdenadas.value.length / props.porPagina)) : 1,
);

const filasVisibles = computed(() => {
  if (props.porPagina <= 0) return filasOrdenadas.value;
  const inicio = (pagina.value - 1) * props.porPagina;
  return filasOrdenadas.value.slice(inicio, inicio + props.porPagina);
});

const rango = computed(() => {
  const total = filasOrdenadas.value.length;
  if (props.porPagina <= 0 || total === 0) return "";
  const desde = (pagina.value - 1) * props.porPagina + 1;
  const hasta = Math.min(pagina.value * props.porPagina, total);
  return `${desde}–${hasta} de ${total}`;
});

watch([busqueda, () => props.filas.length], () => {
  pagina.value = 1;
});

function ordenarPor(columna: ColumnaTabla<F>): void {
  if (orden.value?.clave === columna.clave) {
    orden.value = orden.value.ascendente ? { clave: columna.clave, ascendente: false } : null;
  } else {
    orden.value = { clave: columna.clave, ascendente: true };
  }
}

function ariaOrden(columna: ColumnaTabla<F>): "ascending" | "descending" | undefined {
  if (orden.value?.clave !== columna.clave) return undefined;
  return orden.value.ascendente ? "ascending" : "descending";
}

function claveDe(fila: F, indice: number): string | number {
  const valor = campo(fila, props.claveFila);
  return typeof valor === "string" || typeof valor === "number" ? valor : indice;
}
</script>

<template>
  <div class="data-table">
    <div v-if="buscable" class="data-table__buscador">
      <label :for="idBuscador" class="solo-lector">{{ placeholderBusqueda }}</label>
      <Search class="data-table__icono-buscar" aria-hidden="true" />
      <input
        :id="idBuscador"
        v-model="busqueda"
        type="search"
        class="data-table__input-buscar"
        :placeholder="placeholderBusqueda"
        autocomplete="off"
      />
    </div>

    <table class="data-table__tabla" :aria-label="descripcion">
      <thead>
        <tr>
          <th
            v-for="columna in columnas"
            :key="columna.clave"
            scope="col"
            :aria-sort="ariaOrden(columna)"
          >
            <button
              v-if="columna.ordenable !== false && filas.length > 1"
              type="button"
              class="data-table__ordenar"
              @click="ordenarPor(columna)"
            >
              {{ columna.etiqueta }}
              <ArrowUp v-if="ariaOrden(columna) === 'ascending'" aria-hidden="true" />
              <ArrowDown v-else-if="ariaOrden(columna) === 'descending'" aria-hidden="true" />
            </button>
            <template v-else>{{ columna.etiqueta }}</template>
          </th>
          <th v-if="$slots.acciones" scope="col" class="data-table__col-acciones">Acciones</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(fila, indice) in filasVisibles" :key="claveDe(fila, indice)">
          <td v-for="columna in columnas" :key="columna.clave" :data-etiqueta="columna.etiqueta">
            <slot :name="`celda-${columna.clave}`" :fila="fila">
              {{ campo(fila, columna.clave) }}
            </slot>
          </td>
          <td v-if="$slots.acciones" class="data-table__col-acciones">
            <slot name="acciones" :fila="fila" />
          </td>
        </tr>
      </tbody>
    </table>

    <p v-if="busqueda && filasFiltradas.length === 0" class="data-table__sin-resultados">
      Nada coincide con “{{ busqueda }}”.
    </p>

    <nav v-if="totalPaginas > 1" class="data-table__paginacion" aria-label="Páginas de la tabla">
      <span class="data-table__rango">{{ rango }}</span>
      <div class="data-table__botones-pagina">
        <button
          type="button"
          class="data-table__pagina"
          :disabled="pagina === 1"
          aria-label="Página anterior"
          @click="pagina--"
        >
          <ChevronLeft aria-hidden="true" />
        </button>
        <button
          type="button"
          class="data-table__pagina"
          :disabled="pagina === totalPaginas"
          aria-label="Página siguiente"
          @click="pagina++"
        >
          <ChevronRight aria-hidden="true" />
        </button>
      </div>
    </nav>
  </div>
</template>

<style scoped>
/* Fila con línea inferior, nunca una tarjeta con sombra (sección 15.4).
   Mobile-first: en el teléfono cada fila es un bloque — la primera
   columna como título y el resto como pares etiqueta/valor —, porque una
   tabla de cinco columnas no cabe en 360px sin desplazamiento lateral.
   Desde 48rem vuelve a ser una tabla normal. */
.data-table {
  background: var(--color-papel);
  border: 1px solid var(--color-linea);
  border-radius: var(--radio-lg);
}

.data-table__buscador {
  position: relative;
  padding: var(--espacio-md);
  border-bottom: 1px solid var(--color-linea);
}

.data-table__icono-buscar {
  position: absolute;
  left: calc(var(--espacio-md) + 0.75rem);
  top: 50%;
  transform: translateY(-50%);
  width: 1.1rem;
  height: 1.1rem;
  color: var(--color-tinta-suave);
  pointer-events: none;
}

.data-table__input-buscar {
  width: 100%;
  min-height: var(--area-tactil-minima);
  padding: 0 0.75rem 0 2.5rem;
  border: 1px solid var(--color-borde-campo);
  border-radius: var(--radio-md);
  background: var(--color-papel);
  font-size: var(--texto-base);
}

.data-table__input-buscar:focus-visible {
  outline: 2px solid var(--color-accion);
  outline-offset: 1px;
}

.data-table__tabla {
  width: 100%;
  border-collapse: collapse;
}

.data-table__tabla thead {
  /* En el teléfono cada celda ya lleva su etiqueta; el encabezado queda
     solo para lectores de pantalla. */
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
}

.data-table__tabla tbody,
.data-table__tabla tr,
.data-table__tabla td {
  display: block;
}

.data-table__tabla tr {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: var(--espacio-sm) var(--espacio-lg);
  padding: var(--espacio-md) var(--espacio-lg);
  border-bottom: 1px solid var(--color-linea);
}

.data-table__tabla tbody tr:last-child {
  border-bottom: none;
}

.data-table__tabla td {
  min-width: 0;
  overflow-wrap: anywhere;
  font-size: var(--texto-sm);
}

.data-table__tabla td::before {
  content: attr(data-etiqueta);
  display: block;
  font-size: var(--texto-xs);
  color: var(--color-tinta-suave);
}

.data-table__tabla td:first-child {
  grid-column: 1 / -1;
  font-size: var(--texto-base);
  font-weight: 600;
}

.data-table__tabla td:first-child::before {
  display: none;
}

.data-table__tabla td.data-table__col-acciones {
  grid-column: 1 / -1;
  display: flex;
  flex-wrap: wrap;
  gap: var(--espacio-xs);
  margin-left: calc(-1 * var(--espacio-sm));
}

.data-table__tabla td.data-table__col-acciones::before {
  display: none;
}

.data-table__ordenar {
  display: inline-flex;
  align-items: center;
  gap: var(--espacio-xs);
  padding: 0;
  background: none;
  border: none;
  font-weight: inherit;
  color: inherit;
  cursor: pointer;
}

.data-table__ordenar:hover {
  color: var(--color-tinta);
}

.data-table__ordenar svg {
  width: 0.9rem;
  height: 0.9rem;
}

.data-table__sin-resultados {
  margin: 0;
  padding: var(--espacio-xl) var(--espacio-lg);
  text-align: center;
  color: var(--color-tinta-suave);
}

.data-table__paginacion {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--espacio-md);
  padding: var(--espacio-xs) var(--espacio-sm) var(--espacio-xs) var(--espacio-lg);
  border-top: 1px solid var(--color-linea);
}

.data-table__rango {
  font-size: var(--texto-sm);
  color: var(--color-tinta-suave);
  font-variant-numeric: tabular-nums;
}

.data-table__botones-pagina {
  display: flex;
}

.data-table__pagina {
  display: grid;
  place-items: center;
  width: var(--area-tactil-minima);
  height: var(--area-tactil-minima);
  background: none;
  border: none;
  border-radius: var(--radio-md);
  color: var(--color-tinta);
  cursor: pointer;
}

.data-table__pagina:hover:not(:disabled) {
  background: var(--color-hover);
}

.data-table__pagina:disabled {
  color: var(--color-linea-fuerte);
  cursor: not-allowed;
}

.data-table__pagina svg {
  width: 1.25rem;
  height: 1.25rem;
}

@media (min-width: 48rem) {
  .data-table__tabla thead {
    position: static;
    width: auto;
    height: auto;
    overflow: visible;
    clip: auto;
    display: table-header-group;
  }

  .data-table__tabla tbody {
    display: table-row-group;
  }

  .data-table__tabla tr {
    display: table-row;
    padding: 0;
  }

  .data-table__tabla th {
    text-align: left;
    font-weight: 600;
    font-size: var(--texto-sm);
    color: var(--color-tinta-suave);
    padding: var(--espacio-md) var(--espacio-lg);
    border-bottom: 1px solid var(--color-linea);
    white-space: nowrap;
  }

  .data-table__tabla td,
  .data-table__tabla td:first-child {
    display: table-cell;
    padding: var(--espacio-md) var(--espacio-lg);
    border-bottom: 1px solid var(--color-linea);
    vertical-align: middle;
    font-size: var(--texto-sm);
    font-weight: 400;
  }

  .data-table__tabla td:first-child {
    font-weight: 600;
  }

  .data-table__tabla tbody tr:last-child td {
    border-bottom: none;
  }

  .data-table__tabla td::before {
    display: none;
  }

  .data-table__tabla tbody tr:hover {
    background: var(--color-fondo);
  }

  .data-table__tabla th.data-table__col-acciones,
  .data-table__tabla td.data-table__col-acciones {
    display: table-cell;
    margin: 0;
    text-align: right;
    white-space: nowrap;
  }
}
</style>
