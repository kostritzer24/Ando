# ADR-0006: El Reporte de conducta se estructura según el formato físico `docs/reporte.docx`

**Fecha:** 2026-09-20
**Estado:** Aceptado

## Contexto

El Capítulo IV describe `Reporte de conducta` con solo cuatro atributos genéricos: `inscripción, fecha, descripción, emitido por`. La dirección proporcionó el formato real que usa el centro (`docs/reporte.docx`, "REPORTE DE INCIDENCIA"), que es bastante más estructurado: tipo de falta (leve/grave/muy grave), un catálogo de artículos incumplidos organizado en 5 capítulos del código de convivencia, hechos ocurridos, medidas inmediatas, tipo de sanción aplicada de una lista fija, compromisos establecidos, y firmas de maestro guía, miembro de dirección, estudiante y encargado — estas últimas en papel, nunca digitales (coherente con RN-15).

## Opciones consideradas

1. **Dejar `ConductReport` con el campo `description` genérico del Capítulo IV** y tratar el formato de `reporte.docx` como un simple layout de impresión que arma el texto libre en un PDF con esa estructura visual, sin columnas propias.
2. **Ampliar `ConductReport` con columnas estructuradas** que reflejen cada sección del formato real, y agregar un catálogo nuevo (`catalog.ConductRuleArticle`) para los artículos del código de convivencia, con una tabla de unión (`communication.ConductReportArticle`).

La opción 1 es más barata de modelar pero rompe RF-35 ("consultar los reportes de conducta") de forma útil: una familia necesita ver qué tipo de falta fue y qué sanción se aplicó, no un bloque de texto libre que imite el PDF. También impide filtrar o reportar por gravedad o por artículo incumplido, algo que Dirección va a querer para sus propios informes.

## Decisión

Se amplía `ConductReport` con columnas estructuradas (`severity`, `incident_description`, `immediate_actions`, `sanction_type`, `sanction_detail`, `commitments`, `guide_teacher_id`, `direction_member_id`) y se agrega `catalog.ConductRuleArticle` como octavo dato maestro parametrizable, con `communication.ConductReportArticle` como tabla de unión. El detalle completo de columnas está en `docs/modelo-datos.md`, sección 3.

No se guarda ninguna firma digital ni imagen de firma escaneada: el PDF que genera el sistema para el reporte de conducta reproduce el formato de `reporte.docx` con los campos ya llenos y las líneas de firma en blanco, para imprimir y firmar a mano — así lo exige RN-15.

## Consecuencias

- `catalog.ConductRuleArticle` necesita administración desde el portal administrativo igual que los otros 7 catálogos (RF-02), aunque no estaba en la lista original de la sección 9 del prompt maestro. Se siembra inicialmente con los artículos de `reporte.docx` (capítulos I a V).
- El generador de PDF de `documents/` (ADR-0005, WeasyPrint) necesita una plantilla HTML específica para el reporte de conducta que replique el diseño de `reporte.docx`, no solo el genérico de constancias — se construye en la Fase 9/11 junto con el resto de documentos.
- RF-24 (registrar reporte de conducta) pasa a ser un formulario de varios pasos/checklist, no un campo de texto único — esto se refleja en el diseño de la pantalla correspondiente en la Fase 2/11, no solo en el modelo de datos.
- El campo `other_violation_detail` cubre la sección "OTRA FALTA NO ESPECIFICADA" del formato original para los casos que no calzan en el catálogo de artículos.
