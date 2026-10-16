<script setup lang="ts">
import { Download } from "lucide-vue-next";
import { ref } from "vue";

import { descargarReporteConducta } from "@/features/comunicacion/api/comunicacionApi";
import { descargarArchivo } from "@/features/pagos/api/pagosApi";
import { AppButton, EmptyState, TagPill } from "@/shared/components";
import type { ConductReport } from "@/shared/types/models";

/** Reportes de conducta publicados, uno por tarjeta: lo que pasó, qué se
 * hizo y a qué se comprometió el estudiante, con el PDF a un toque. */
defineProps<{ reportes: ConductReport[] }>();

const GRAVEDAD: Record<string, { etiqueta: string; variante: "aviso" | "alerta" | "neutro" }> = {
  leve: { etiqueta: "Falta leve", variante: "neutro" },
  grave: { etiqueta: "Falta grave", variante: "aviso" },
  muy_grave: { etiqueta: "Falta muy grave", variante: "alerta" },
};
const SANCION: Record<string, string> = {
  llamado_verbal: "Llamado verbal",
  amonestacion_escrita: "Amonestación escrita",
  comunicacion_familia: "Comunicación a la familia",
  suspension_extracurricular: "Suspensión de actividades extracurriculares",
  servicio_comunitario: "Servicio comunitario",
  suspension_clases: "Suspensión de clases",
  evaluacion_expulsion: "Evaluación para expulsión",
  otra: "Otra medida",
};

const descargando = ref("");
const error = ref("");

function fechaLarga(iso: string): string {
  return new Date(`${iso}T12:00:00`).toLocaleDateString("es-GT", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

function lineas(texto: string): string[] {
  return texto.split("\n").map((l) => l.trim()).filter(Boolean);
}

async function descargar(reporte: ConductReport): Promise<void> {
  descargando.value = reporte.public_id;
  error.value = "";
  try {
    const { blob, nombreArchivo } = await descargarReporteConducta(reporte.public_id);
    descargarArchivo(blob, nombreArchivo);
  } catch {
    error.value = "No se pudo descargar el reporte. Inténtalo de nuevo.";
  } finally {
    descargando.value = "";
  }
}
</script>

<template>
  <div class="reportes-familia">
    <EmptyState
      v-if="reportes.length === 0"
      titulo="No hay reportes de conducta"
      descripcion="Cuando la dirección publique un reporte, va a aparecer aquí."
    />
    <p v-if="error" class="reportes-familia__error" role="alert">{{ error }}</p>

    <article v-for="reporte in reportes" :key="reporte.public_id" class="reportes-familia__tarjeta">
      <header class="reportes-familia__cabecera">
        <time :datetime="reporte.report_date">{{ fechaLarga(reporte.report_date) }}</time>
        <TagPill :variante="GRAVEDAD[reporte.severity]?.variante ?? 'neutro'">
          {{ GRAVEDAD[reporte.severity]?.etiqueta ?? reporte.severity }}
        </TagPill>
      </header>

      <h4>Qué ocurrió</h4>
      <p>{{ reporte.incident_description }}</p>

      <h4>Qué se hizo</h4>
      <p>{{ reporte.immediate_actions }}</p>
      <p class="reportes-familia__sancion">
        <strong>Medida:</strong> {{ SANCION[reporte.sanction_type] ?? reporte.sanction_type }}
        <template v-if="reporte.sanction_detail"> — {{ reporte.sanction_detail }}</template>
      </p>

      <template v-if="lineas(reporte.commitments).length > 0">
        <h4>Compromisos</h4>
        <ul>
          <li v-for="linea in lineas(reporte.commitments)" :key="linea">{{ linea }}</li>
        </ul>
      </template>

      <AppButton variante="secundario" compacto :deshabilitado="descargando === reporte.public_id" @click="descargar(reporte)">
        <Download :size="16" aria-hidden="true" /> Descargar PDF
      </AppButton>
    </article>
  </div>
</template>

<style scoped>
.reportes-familia {
  display: grid;
  gap: var(--espacio-md);
}

.reportes-familia__tarjeta {
  padding: var(--espacio-md);
  background: var(--color-papel);
  border: 1px solid var(--color-linea);
  border-radius: var(--radio-lg);
}

.reportes-familia__cabecera {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--espacio-sm);
  font-weight: 600;
}

.reportes-familia__tarjeta h4 {
  margin: var(--espacio-md) 0 var(--espacio-2xs);
  font-size: var(--texto-sm);
  color: var(--color-tinta-suave);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.reportes-familia__tarjeta p {
  margin: 0 0 var(--espacio-xs);
  overflow-wrap: anywhere;
}

.reportes-familia__tarjeta ul {
  margin: 0 0 var(--espacio-sm);
  padding-left: 1.25rem;
}

.reportes-familia__sancion {
  margin-top: var(--espacio-xs);
}

.reportes-familia__error {
  color: var(--color-etiqueta-alerta-texto);
}
</style>
