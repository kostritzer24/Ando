<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";

import { tiposDocumentoApi } from "@/features/catalogo/api/catalogoApi";
import { enrollmentsApi, studentsApi } from "@/features/estudiantes/api/estudiantesApi";
import { AppButton, AppPanel, CargandoBloque, DataTable, EmptyState, ErrorBanner, FormField, FormSelect, PageHeader } from "@/shared/components";
import { usePermisos } from "@/shared/permisos";
import type { DocumentType, Enrollment, IssuedDocument, Student } from "@/shared/types/models";

import { descargarArchivo, descargarDocumento, emitirDocumento, issuedDocumentsApi } from "../api/pagosApi";

const permisos = usePermisos();
const puedeEmitir = computed(() => permisos.puedeEditar("documentos"));

const cargando = ref(true);
const error = ref("");
const documentos = ref<IssuedDocument[]>([]);
const inscripciones = ref<Enrollment[]>([]);
const estudiantes = ref<Student[]>([]);
const tiposDocumento = ref<DocumentType[]>([]);

const opcionesInscripcion = computed(() =>
  inscripciones.value.map((i) => {
    const estudiante = estudiantes.value.find((e) => e.public_id === i.student);
    const nombre = estudiante ? `${estudiante.first_name} ${estudiante.last_name}` : "—";
    const codigo = estudiante ? ` (${estudiante.internal_code})` : "";
    return { valor: i.public_id, etiqueta: `${nombre}${codigo}` };
  }),
);

const opcionesTipo = computed(() =>
  tiposDocumento.value
    .filter((t) => t.template_key !== "constancia_solvencia" && t.is_active !== false)
    .map((t) => ({ valor: t.public_id, etiqueta: t.name })),
);

const formulario = reactive({ enrollment: "", document_type: "", custom_text: "" });
const esCartaMembretada = computed(
  () => tiposDocumento.value.find((t) => t.public_id === formulario.document_type)?.template_key === "carta_membretada",
);

const emitiendo = ref(false);
const errorEmision = ref("");
const descargandoId = ref("");

async function cargar(): Promise<void> {
  cargando.value = true;
  error.value = "";
  try {
    const [documentosResp, inscripcionesResp, estudiantesResp] = await Promise.all([
      issuedDocumentsApi.listar(),
      enrollmentsApi.listar(),
      studentsApi.listar(),
    ]);
    documentos.value = documentosResp.results;
    inscripciones.value = inscripcionesResp.results.filter((i) => i.status === "activo");
    estudiantes.value = estudiantesResp.results;

    if (puedeEmitir.value) {
      tiposDocumento.value = (await tiposDocumentoApi.listar()).results;
      formulario.enrollment = opcionesInscripcion.value[0]?.valor ?? "";
      formulario.document_type = opcionesTipo.value[0]?.valor ?? "";
    }
  } catch {
    error.value = "No se pudo cargar la bandeja de documentos. Probá de nuevo.";
  } finally {
    cargando.value = false;
  }
}

function nombreEstudiante(enrollmentPublicId: string): string {
  const inscripcion = inscripciones.value.find((i) => i.public_id === enrollmentPublicId);
  const estudiante = inscripcion ? estudiantes.value.find((e) => e.public_id === inscripcion.student) : undefined;
  return estudiante ? `${estudiante.first_name} ${estudiante.last_name}` : "—";
}

async function emitir(): Promise<void> {
  emitiendo.value = true;
  errorEmision.value = "";
  try {
    const { blob, nombreArchivo } = await emitirDocumento({
      enrollment: formulario.enrollment,
      document_type: formulario.document_type,
      custom_text: esCartaMembretada.value ? formulario.custom_text : "",
    });
    descargarArchivo(blob, nombreArchivo);
    formulario.custom_text = "";
    documentos.value = (await issuedDocumentsApi.listar()).results;
  } catch {
    errorEmision.value = "No se pudo emitir el documento. Revisá los datos e intentá de nuevo.";
  } finally {
    emitiendo.value = false;
  }
}

async function volverADescargar(documento: IssuedDocument): Promise<void> {
  descargandoId.value = documento.public_id;
  try {
    const { blob, nombreArchivo } = await descargarDocumento(documento.public_id);
    descargarArchivo(blob, nombreArchivo);
  } catch {
    error.value = "No se pudo descargar el documento. Probá de nuevo.";
  } finally {
    descargandoId.value = "";
  }
}

onMounted(cargar);
</script>

<template>
  <section class="documentos-page">
    <PageHeader
      titulo="Documentos emitidos"
      descripcion="Constancias y cartas con código de verificación. Se pueden volver a descargar cuando haga falta."
    />

    <ErrorBanner v-if="error" :mensaje="error" etiqueta-accion="Reintentar" @accion="cargar" />
    <CargandoBloque v-else-if="cargando" />

    <div v-else class="documentos-page__paneles" :class="{ 'documentos-page__paneles--uno': !puedeEmitir }">
      <AppPanel v-if="puedeEmitir" titulo="Emitir documento">
        <form class="documentos-page__formulario" @submit.prevent="emitir">
          <ErrorBanner v-if="errorEmision" :mensaje="errorEmision" />
          <FormSelect
            id="enrollment"
            etiqueta="Estudiante"
            :opciones="opcionesInscripcion"
            v-model="formulario.enrollment"
          />
          <FormSelect
            id="document_type"
            etiqueta="Tipo de documento"
            :opciones="opcionesTipo"
            v-model="formulario.document_type"
          />
          <FormField
            v-if="esCartaMembretada"
            id="custom_text"
            etiqueta="Texto de la carta"
            multilinea
            v-model="formulario.custom_text"
          />
          <AppButton
            tipo="submit"
            bloque
            :deshabilitado="emitiendo || !formulario.enrollment || !formulario.document_type"
          >
            {{ emitiendo ? "Generando…" : "Emitir" }}
          </AppButton>
        </form>
      </AppPanel>

      <section class="documentos-page__bandeja" aria-labelledby="titulo-bandeja">
        <h2 id="titulo-bandeja" class="documentos-page__subtitulo">Bandeja de documentos</h2>
        <EmptyState
          v-if="documentos.length === 0"
          titulo="No hay documentos emitidos"
          descripcion="Los documentos que se emitan van a aparecer acá."
        />
        <DataTable
          v-else
          :columnas="[
            { clave: 'estudiante', etiqueta: 'Estudiante' },
            { clave: 'document_type', etiqueta: 'Tipo' },
            { clave: 'fecha', etiqueta: 'Emitido' },
            { clave: 'verification_code', etiqueta: 'Código' },
          ]"
          :filas="
            documentos.map((d) => ({
              ...d,
              estudiante: nombreEstudiante(d.enrollment),
              fecha: new Date(d.issued_at).toLocaleDateString('es-GT'),
            }))
          "
          buscable
          placeholder-busqueda="Buscar documento"
          descripcion="Documentos emitidos"
        >
          <template #acciones="{ fila }">
            <AppButton
              variante="discreto"
              compacto
              :deshabilitado="descargandoId === (fila as unknown as IssuedDocument).public_id"
              @click="volverADescargar(fila as unknown as IssuedDocument)"
            >
              Volver a descargar
            </AppButton>
          </template>
        </DataTable>
      </section>
    </div>
  </section>
</template>

<style scoped>
.documentos-page__paneles {
  display: grid;
  gap: var(--espacio-2xl);
  align-items: start;
}

.documentos-page__formulario {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-lg);
}

.documentos-page__bandeja {
  min-width: 0;
}

.documentos-page__subtitulo {
  font-size: var(--texto-md);
  margin-bottom: var(--espacio-md);
}

@media (min-width: 64rem) {
  .documentos-page__paneles {
    grid-template-columns: 22rem minmax(0, 1fr);
  }

  .documentos-page__paneles--uno {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
