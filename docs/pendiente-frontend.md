# Frontend pendiente

Desde la Fase 4 en adelante, el trabajo avanza backend primero por fase; el frontend de negocio se construye en un bloque aparte más adelante (decisión del equipo, ver `docs/fase-4-cierre.md`). Este documento lleva la cuenta de qué pantallas quedan debiendo cada fase, para que esa pasada de frontend no tenga que releer todo el histórico de commits.

**El bloque arrancó al cerrar la Fase 9** (Pagos, solvencia y documentos), como estaba decidido: la Fase 9 fue la última fase mayormente de backend del plan (sección 18 del prompt maestro); la Fase 10 (portal público) y la Fase 11 (comunicación) son trabajo de interfaz por naturaleza, así que construir el frontend justo antes evita hacerlo dos veces — y la Fase 10 se construye directamente con su propio frontend, sin separarle un "backend primero" artificial. Va fase por fase, con el mismo criterio de verificación en vivo que se usó en el backend (ver `docs/fase-4-frontend-cierre.md` para la primera).

La Fase 3 es la excepción: su frontend (login, cambio de contraseña, guards por rol) ya está construido — ver `docs/fase-3-cimientos-plan.md`.

## Pendiente

Portal público (familia): RF-31 (consultar asistencia, datos reales desde la Fase 6), RF-33 (consultar solvencia y descargar constancia, datos reales desde la Fase 9) y RF-34 (descargar boletín publicado, datos reales desde la Fase 9) ya tienen todo lo que necesitan del backend — esas pantallas específicas son Fase 10, no se construyen todavía.

## Hecho

- **Fase 3** — Login, cambio de contraseña obligatorio, guards de router por rol. (`frontend/src/features/auth/`)
- **Fase 4** — Datos maestros: los 8 catálogos, portal administrativo, Dirección/Administrador editan y Coordinación solo ve (los botones de escritura se esconden para ese rol). Cierre completo en `docs/fase-4-frontend-cierre.md`. (`frontend/src/features/catalogo/`)
- **Fase 5** — Expedientes y asignaciones: inscribir estudiante, expediente con datos sensibles restringidos, encargados (con la creación del usuario de la cuenta familiar incluida en el mismo formulario) y sus vínculos, asignación de docente/tallerista con el curso y la persona filtrados por tipo de sección. Cierre completo en `docs/fase-5-frontend-cierre.md`. (`frontend/src/features/estudiantes/`, `frontend/src/features/asignaciones/`)
- **Fase 6** — Asistencia: tomar asistencia por sección (con hora de llegada o estado directo), justificaciones (registrar y resolver), plantilla de talleres. Primer portal operativo con layout propio (`OperativoLayout`). Cierre completo en `docs/fase-6-frontend-cierre.md`. (`frontend/src/features/asistencia/`)
- **Fase 7** — Notas: diseñar la unidad (con el total de puntos y de pruebas cortas en vivo), capturar punteo (con "solicitar corrección" en vez de editar directo, RN-05), plantilla de calificaciones con vista previa de dos pasos, bandeja de modificaciones (propia y, para Dirección, aprobar/rechazar). `raw_score` no aparece en ninguna pantalla — la API no lo expone. Cierre completo en `docs/fase-7-frontend-cierre.md`. (`frontend/src/features/notas/`)
- **Fase 8** — Horarios y calendario: grilla de horario por docente/tallerista (Dirección), horario propio de solo lectura, calendario compartido entre los dos portales con avisos institucionales (Dirección) y eventos propios (docente/guía/tallerista). Cierre completo en `docs/fase-8-frontend-cierre.md`. (`frontend/src/features/horarios/`)
- **Fase 9** — Pagos, solvencia y documentos: registrar pago, consultar solvencia y emitir constancia de solvencia (Dirección/Pagos), emitir constancias de estudio/conducta y cartas membretadas con bandeja de "volver a descargar" (Dirección emite, Pagos solo ve sus propias constancias de solvencia — alcance que ya filtra el backend), bandeja de boletines por sección/unidad con generar/aprobar/publicar y los mensajes de RN-09/RN-10 tal como los devuelve el backend (Dirección). Cierre completo en `docs/fase-9-frontend-cierre.md`. (`frontend/src/features/pagos/`)
