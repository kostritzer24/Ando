# Frontend pendiente

Desde la Fase 4 en adelante, el trabajo avanza backend primero por fase; el frontend de negocio se construye en un bloque aparte más adelante (decisión del equipo, ver `docs/fase-4-cierre.md`). Este documento lleva la cuenta de qué pantallas quedan debiendo cada fase, para que esa pasada de frontend no tenga que releer todo el histórico de commits.

**El bloque arrancó al cerrar la Fase 9** (Pagos, solvencia y documentos), como estaba decidido: la Fase 9 fue la última fase mayormente de backend del plan (sección 18 del prompt maestro); la Fase 10 (portal público) y la Fase 11 (comunicación) son trabajo de interfaz por naturaleza, así que construir el frontend justo antes evita hacerlo dos veces — y la Fase 10 se construye directamente con su propio frontend, sin separarle un "backend primero" artificial. Va fase por fase, con el mismo criterio de verificación en vivo que se usó en el backend (ver `docs/fase-4-frontend-cierre.md` para la primera).

La Fase 3 es la excepción: su frontend (login, cambio de contraseña, guards por rol) ya está construido — ver `docs/fase-3-cimientos-plan.md`.

## Pendiente

Portal operativo (Fase 6+): `GET /assignments/` ya llega filtrado a "mis asignaciones" por el backend (`scope_queryset`, sin necesidad de un parámetro `?mine=`) para que un docente/tallerista vea qué tiene asignado — insumo para las pantallas de asistencia y notas, no hace falta una pantalla dedicada solo para esto.

### Fase 6 — Asistencia (RF-16, RF-12, RF-21)
Portal operativo, rol Docente/Docente con sección a cargo/Tallerista (siempre limitado a sus propias secciones asignadas, el backend ya lo filtra):

- Tomar asistencia diaria de una sección: lista de inscritos con un selector rápido presente/tarde/ausente/justificado por estudiante — HU-16 pide que se pueda hacer durante la clase o al final de la jornada, así que el diseño tiene que permitir guardar parcial y volver
- Si se captura hora de llegada en vez de estado directo, mandar `check_in_time` y dejar que el backend decida presente/tarde (RN-11) — no calcular la tardanza en el frontend
- Pantalla de justificaciones: registrar una (con archivo adjunto opcional) y, para Dirección, resolver (aprobar/rechazar) — la resolución es la única acción restringida a Dirección en toda esta fase
- El documento de respaldo de una justificación se descarga con `GET /justifications/{id}/document/`, nunca con una URL directa (no hay `MEDIA_URL` público a propósito)

Portal administrativo/operativo, para secciones de taller (RF-21):
- Botón "Descargar plantilla" (`GET /attendance/template/{section}/{fecha}/`) y "Subir plantilla" (`POST /attendance/template/upload/`) — la subida devuelve una lista de errores por fila si algo no cuadra (ningún registro se guarda hasta que el archivo esté limpio); el diseño de esta pantalla de errores debe seguir el principio de "vista previa que no es un volcado técnico" de la sección 15.2 del prompt maestro

Portal público (familia), ya con datos reales disponibles para RF-31 (consultar asistencia) — todavía no construido porque esa pantalla específica es Fase 10.

### Fase 7 — Notas (RF-17 a RF-20, RF-23, RF-10)
Portal operativo, rol Docente/Docente con sección a cargo (siempre limitado a sus propias asignaciones, el backend ya lo filtra):

- Diseñar la unidad: agregar actividades una por una viendo en todo momento cuántos puntos van (de 100) y cuántas son pruebas cortas — el backend rechaza pasarse de 100, pero la pantalla debería impedirlo visualmente antes de mandar la petición, no solo mostrar el error
- Capturar punteo real por actividad, uno por uno — si la actividad ya tiene nota, no ofrecer "editar" directo: llevar al formulario de "solicitar corrección" (RF-23), porque el backend ya rechaza el sobrescritura (RN-05)
- Botones "Descargar plantilla" (`GET /grades/template/{assignment}/{unit}/`) y "Subir plantilla", con un paso de vista previa (`POST /grades/template/preview/`) antes de confirmar (`POST /grades/template/upload/`) — la vista previa distingue notas nuevas de modificaciones, así que la pantalla debería mostrar esa distinción, no solo un número total
- Bandeja de solicitudes de modificación propias, con su estado (pendiente/aprobada/rechazada)

Portal administrativo, rol Dirección:
- Bandeja de solicitudes de modificación pendientes de todo el centro, con aprobar/rechazar (`POST /grade-change-requests/{id}/approve|reject/`) — es la única acción de escritura de toda esta fase que no es del docente

Ninguna pantalla debe mostrar `raw_score` en ningún rol — la API ya no lo expone (RN-06), así que no hay manera de mostrarlo aunque alguien lo pidiera; si Dirección necesita ver el historial de una nota, es a través de `original_score`/`requested_score` en la solicitud de modificación, no de un campo "punteo real" suelto.

### Fase 8 — Horarios y calendario (RF-06, RF-22, RF-26)
Portal administrativo, rol Dirección (única que escribe horario, `docs/api.md` documenta `/assignments/` y `/schedule-blocks/` como `DIR (E)`):

- Grilla de horario día × período (lunes a viernes, 6 períodos, RN-13) para armar/editar el horario de todo el centro — al elegir docente y curso-sección, si `POST /schedule-blocks/` devuelve el error de cruce (RN-13/HU-06), resaltar en la grilla la celda donde ese docente ya tiene clase ese día, no solo mostrar el texto del error
- El formulario debe ofrecer solo asignaciones (`assignment`) ya existentes — no se crea la asignación docente↔curso-sección desde esta pantalla, eso es de Fase 5

Portal operativo, rol Docente/Docente con sección a cargo/Tallerista:
- Vista de solo lectura de `GET /schedule/mine/`: horario propio en formato de grilla o lista por día — Dirección no tiene acceso a esta ruta (403 por diseño, ve el horario completo desde la grilla administrativa en su lugar)
- Calendario: publicar un evento propio (`POST /calendar-events/`), tipo "asignación docente", opcionalmente ligado a una de sus asignaciones — el formulario no debe ofrecer la opción "institucional" a estos roles, porque el backend la rechaza (RN-17)
- Editar/eliminar solo los eventos que uno mismo publicó — un evento institucional puede aparecer en la lista (es visible) pero sin botones de editar/eliminar para estos roles; intentar la URL directa da 403, no hay necesidad de manejarlo especial en el frontend más que no ofrecer el botón

Portal administrativo, rol Dirección:
- Publicar eventos institucionales además de los propios; editar o eliminar cualquier evento del calendario (única combinación de rol que puede tocar eventos ajenos)

Portal público, calendario institucional de solo lectura — ya con datos reales disponibles, pero esa pantalla específica corresponde a una fase posterior del portal público, no a esta.

### Fase 9 — Pagos, solvencia y documentos (RF-07 a RF-09, RF-11, RF-14)
Portal administrativo, rol Encargado de pagos / Dirección:

- Registrar un pago (`POST /payments/`): mes, año, monto, fecha de pago, número de recibo — sin edición ni baja posterior, es un comprobante, no un borrador (ver `docs/fase-9-cierre.md`)
- Consultar el estado de solvencia de un estudiante (`GET /solvency/{enrollment}/`) con el detalle de meses pendientes, y el botón "Emitir constancia de solvencia" (`POST /solvency/{enrollment}/certificate/`) — deshabilitado o con aviso claro cuando el estudiante no está solvente, porque el backend lo rechaza (RN-08)
- Emitir constancias de estudio, de buena conducta y cartas membretadas (`POST /documents/issue/`) — el formulario de carta membretada es el único con un campo de texto libre; los otros tres tipos no piden nada más que elegir el estudiante
- Bandeja de documentos ya emitidos, con "volver a descargar" (`GET /documents/{id}/download/`) en vez de regenerar

Portal operativo, rol Dirección:
- Bandeja de boletines por sección/unidad: "Generar" (`POST /report-cards/generate/`, por lote) deja cada boletín en borrador; "Aprobar" y "Publicar" actúan uno por uno — la pantalla debe mostrar por qué un boletín no se puede publicar todavía (RN-10: falta el plazo; RN-09: el estudiante no está solvente) con el mensaje que ya devuelve el backend, no uno inventado en el frontend

Portal público (familia), ya con datos reales disponibles para RF-33 (consultar solvencia y descargar constancia) y RF-34 (descargar boletín publicado) — no se construyen todavía porque esas pantallas específicas son Fase 10.

Nota transversal: los cuatro documentos PDF (constancia de solvencia, de estudio, de conducta y carta membretada) ya se generan con el membrete institucional, código QR y espacio para firma/sello a mano (RN-15) desde el backend — no hace falta ningún trabajo de diseño de documento en el frontend, solo el botón que dispara la descarga.

## Hecho

- **Fase 3** — Login, cambio de contraseña obligatorio, guards de router por rol. (`frontend/src/features/auth/`)
- **Fase 4** — Datos maestros: los 8 catálogos, portal administrativo, Dirección/Administrador editan y Coordinación solo ve (los botones de escritura se esconden para ese rol). Cierre completo en `docs/fase-4-frontend-cierre.md`. (`frontend/src/features/catalogo/`)
- **Fase 5** — Expedientes y asignaciones: inscribir estudiante, expediente con datos sensibles restringidos, encargados (con la creación del usuario de la cuenta familiar incluida en el mismo formulario) y sus vínculos, asignación de docente/tallerista con el curso y la persona filtrados por tipo de sección. Cierre completo en `docs/fase-5-frontend-cierre.md`. (`frontend/src/features/estudiantes/`, `frontend/src/features/asignaciones/`)
