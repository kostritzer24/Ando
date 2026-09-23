# Fase 6 (frontend) — Asistencia: cierre

Tercera fase del bloque de frontend, y la primera con pantallas reales en el portal operativo — hasta ahora ese portal solo tenía la página de inicio de la Fase 3. Cubre RF-16, RF-12, RF-21: asistencia diaria, justificaciones y plantilla de talleres.

## Qué se construyó

- **`OperativoLayout.vue`**: primer layout del portal operativo (barra lateral + navegación por rol, igual que `AdministrativoLayout` de la Fase 4 — mismo `AdminShell` reutilizado en los dos portales de escritorio).
- **`TomarAsistenciaPage.vue`**: por sección y fecha, cada estudiante tiene cuatro botones de estado (presente/tarde/ausente/justificado) que guardan apenas se tocan — sin botón de "guardar todo" — para cumplir HU-16 ("durante la clase o al final de la jornada, guardar parcial y volver"). Si todavía no hay registro para ese estudiante ese día, también aparece un campo de hora de llegada: mandarlo hace que el backend decida presente/tarde (RN-11), nunca el frontend.
- **`JustificacionesPage.vue`**: registrar una justificación (con documento de respaldo opcional) eligiendo entre las propias faltas/tardanzas sin justificar; Dirección además puede aprobar/rechazar. El documento se descarga como blob autenticado (`GET /justifications/{id}/document/`) y se dispara con un enlace sintético — nunca una URL directa, no hay `MEDIA_URL` público a propósito.
- **`PlantillaAsistenciaPage.vue`** (RF-21): descargar la plantilla de un taller y subirla llena, mostrando los errores por fila tal como los devuelve el backend, sin volcado técnico.
- Dirección llega a las cuatro pantallas también desde el portal administrativo (RN footnote 4 de `docs/permisos-roles.md`: "Dirección registra asistencia matutina aunque el módulo pertenezca al portal operativo") — mismos componentes, rutas nuevas bajo `/administrativo/`.

## Bug real encontrado y corregido: un docente no podía ver el nombre de su propia sección

Al armar el selector de secciones para `TomarAsistenciaPage`, `GET /sections/` devolvió 403 para `docente.demo`. La razón: `/sections/` (y `/courses/`) viven detrás del área "datos_maestros", donde el rol Docente tiene `sin_acceso` — una restricción deliberada de la Fase 1 (administrar el catálogo es cosa de Dirección/Coordinación/Administrador), pero que de paso le bloqueaba también la simple *lectura* del grado y la letra de su propia sección.

Se corrigió sin abrirle el catálogo completo a nadie: `TeacherAssignmentSerializer` ahora incluye `section_grade`, `section_letter`, `section_type` y `course_name` de solo lectura, sacados de la asignación que el docente ya puede consultar (`/assignments/`, scoped a "las suyas"). El frontend arma la lista de secciones a partir de sus propias asignaciones en vez de pedir el catálogo — Dirección, que sí tiene acceso a "datos_maestros", sigue viendo la lista completa por el camino de siempre.

## Bug real encontrado y corregido: nadie sin acceso a "datos maestros" podía elegir un tipo de justificación

Mismo síntoma, causa distinta: `GET /justification-types/` también vive detrás de "datos_maestros", así que ni un docente ni un tallerista podían cargar las opciones del selector "Tipo de justificación" al registrar una — un catálogo administrativo bloqueando una acción operativa explícitamente pedida por RF-12. Como no hay ningún recurso propio del docente del que colgar esta info (a diferencia de la sección/curso, que sí cuelgan de la asignación), se aplicó el mismo patrón que ya usa `GradeChangeRequestViewSet` desde la Fase 7 del backend: el área cambia según la acción. Leer (`list`/`retrieve`) pasa por "asistencia", donde Docente/Guía/Tallerista sí tienen alcance; administrar el catálogo (crear/editar/dar de baja) sigue siendo exclusivo de "datos_maestros", igual que los otros siete catálogos.

## Verificación real

6 pruebas nuevas de backend (dos por cada gap corregido, más las de alcance existentes) y 4 pruebas de extremo a punta contra un navegador real: tomar asistencia con los botones de estado y confirmar que sobrevive a un recargo de página, corregir un estado ya guardado (PATCH, no un segundo POST — `Attendance` tiene `unique(enrollment, date)`), registrar la hora de llegada y ver que el sistema decide "tarde" sin que el frontend haga el cálculo, registrar una justificación como docente y resolverla como Dirección, y descargar la plantilla de un taller. `vue-tsc --noEmit` y `eslint` sin errores; 287 pruebas de backend en verde.

## Siguiente

Fase 7 (frontend) — Notas: diseño de unidad, captura de punteo, plantilla de calificaciones con vista previa, bandeja de modificaciones. Detalle completo en `docs/pendiente-frontend.md`.
