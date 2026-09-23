# Fase 7 (frontend) — Notas: cierre

Cuarta fase del bloque de frontend. Cubre RF-17 a RF-20, RF-23, RF-10: diseño de unidad, captura de punteo, plantilla de calificaciones y modificaciones de nota. La misma fase que el propio prompt maestro señala como la más sensible del proyecto (Fase 7 del backend, `docs/fase-7-cierre.md`) — acá se trató con el mismo cuidado.

## Qué se construyó

- **`UnidadPage.vue`** (RF-17): elegir asignación y unidad, agregar actividades viendo en todo momento cuántos de los 100 puntos van usados y cuántas pruebas cortas lleva (RN-04, mínimo 4) — el botón "Agregar actividad" se deshabilita solo al llegar a 100, sin esperar el error del backend.
- **`CapturarNotasPage.vue`** (RF-18/RF-23): elegir asignación, unidad y actividad, y una fila por estudiante inscrito. Si la actividad todavía no tiene nota, un campo numérico la guarda apenas se pierde el foco (mismo patrón de "guardar solo" que asistencia). Si ya la tiene, no hay forma de editarla directo — el único botón es "Solicitar corrección" (RN-05: el punteo real nunca se sobrescribe).
- **`PlantillaNotasPage.vue`** (RF-19/RF-20): descargar la plantilla de una unidad, y subirla en dos pasos — "Ver antes de guardar" (`POST /grades/template/preview/`) muestra cuántas filas son notas nuevas, cuántas van a generar una solicitud de modificación (RN-07) y cuántas no cambian nada, sin guardar todavía; "Confirmar y guardar" recién ahí llama `POST /grades/template/upload/`.
- **`ModificacionesPage.vue`** (RF-23/RF-10): un solo componente para las dos bandejas — un docente ve sus propias solicitudes (el backend ya las filtra), Dirección ve todas las pendientes con botones de Aprobar/Rechazar. Ninguna pantalla de esta fase muestra `raw_score`: la API nunca lo expone (RN-06), la única nota visible es `current_score`, y el historial de una corrección se ve a través de `original_score`/`requested_score` en la propia solicitud.

## Bugs reales encontrados y corregidos: dos catálogos más bloqueaban una pantalla operativa

Misma familia de bug que ya había aparecido en la Fase 6 con `/justification-types/` — esta vez con dos catálogos más, los dos necesarios para "diseñar la unidad" (RF-17):

- **`/activity-types/`** (tipo de actividad: prueba corta, tarea, proyecto...): un docente no podía leer la lista para elegir un tipo al crear una actividad.
- **`/cycles/{cycle_id}/units/`** (las unidades del ciclo): un docente no podía leer la lista para elegir en qué unidad está diseñando, aunque ya conociera el `cycle_id` por su propia asignación.

Los dos se corrigieron con el mismo patrón ya usado (y ahora consolidado como el criterio del proyecto para este tipo de caso): la lectura (`list`/`retrieve`) de ambos pasa por el área "notas", donde Docente/Guía sí tienen alcance; crear, editar o dar de baja sigue siendo exclusivo de "datos_maestros", igual que el resto de los ocho catálogos.

## Verificación real

4 pruebas nuevas de backend y 3 pruebas de extremo a punta contra un navegador real: diseñar una unidad y ver el total de puntos actualizarse en vivo, capturar una nota, solicitar su corrección, aprobarla como Dirección, y descargar la plantilla de calificaciones. `vue-tsc --noEmit` y `eslint` sin errores; 291 pruebas de backend en verde.

Nota de la prueba en navegador: `fill()` sobre un `<input type="number">` no dispara el evento `change` del navegador hasta que el campo pierde el foco — a diferencia de `<input type="time">` (Fase 6), que sí lo dispara solo con `fill()`. La prueba de captura de notas necesitó un `Tab` explícito después de `fill()` para que el guardado se disparara; el comportamiento real de la aplicación no cambia (cualquier clic posterior de un usuario real ya pierde el foco solo).

## Siguiente

Fase 8 (frontend) — Horarios y calendario: grilla de horario (Dirección), horario propio (docente/guía/tallerista), calendario con avisos institucionales y eventos propios. Detalle completo en `docs/pendiente-frontend.md`.
