# Fase 6 — Asistencia: cierre

Cubre RF-16, RF-12, RF-21, RN-11, RN-12 (sección 18 del prompt maestro). Backend completo y probado; frontend pendiente (misma decisión de secuencia — ver `docs/pendiente-frontend.md`).

## Qué se construyó

- **`attendance`:** `Attendance` y `Justification`, ambos colgando de `Enrollment` — por diseño (ADR-0001), aplican igual a la jornada matutina que a los talleres.
- **RN-11 en código:** `attendance/domain/late_arrival.py` deriva `presente`/`tarde` a partir de la hora de llegada (corte 8:05), probado en los dos sentidos del límite. El registro de asistencia acepta un estado directo o una hora de llegada — nunca ambos como obligatorios, nunca ninguno.
- **RN-12 en código:** `attendance/domain/rights.py` expresa "una falta sin justificar quita el derecho a las actividades del día" como una función pura, lista para que la Fase 7 (notas) la use. Aprobar una justificación cambia la asistencia a `justificado` automáticamente; rechazarla no toca la asistencia.
- **RF-21 con la primera biblioteca externa del proyecto en uso real:** `openpyxl` (confirmada en ADR-0005) genera la plantilla de asistencia de un taller y valida la que se sube — fila por fila, sin guardar nada si hay un solo error (la "vista previa" de la sección 14.4), rechazando explícitamente archivos que no sean `.xlsx`.
- **Alcance por objeto en escritura, no solo en lectura:** un docente/tallerista no puede registrar (ni por plantilla) la asistencia de una sección donde no tiene una asignación vigente — probado como caso de acceso no autorizado.
- **Documentos sensibles nunca por URL pública:** el documento de respaldo de una justificación se sube con la justificación pero se descarga por una acción autenticada (`GET /justifications/{id}/document/`); no hay `MEDIA_URL` servido públicamente en ningún entorno.

## Corrección real encontrada probando en vivo

Al generar la plantilla de un taller con datos de siembra, apareció vacía — y al investigar por qué, se encontró que `Enrollment` tenía `unique(student, cycle)`, heredado literalmente de la lectura de HU-03 en la Fase 5. Esa restricción le impedía a un estudiante tener a la vez su sección académica y una de taller en el mismo ciclo, justo lo que la sección 1 del prompt maestro describe (los participantes de taller son, al menos en parte, los mismos 144 estudiantes de la jornada matutina) y lo que ADR-0001 ya había decidido que debía funcionar.

**Corregido:** la restricción pasa a `unique(student, cycle, section)` (no se puede repetir la misma sección, pero sí tener una académica y una de taller a la vez); la regla real de HU-03 — una sola sección académica por ciclo — se mueve a `students/services/enrollment.py`, porque una restricción de base de datos no puede mirar `Section.type` sin duplicar esa columna en `Enrollment`. Se corrigieron `docs/modelo-datos.md` y ADR-0001, se agregó una migración nueva (no se reescribió la de la Fase 5, ya comprometida), y se agregaron pruebas que cubren explícitamente el caso que se rompía.

**Verificación real:** 154 pruebas (35 nuevas), 98 % de cobertura en `domain/`+`services/`, y un flujo completo en vivo — descargar la plantilla de un taller con un estudiante real inscrito, llenarla, subirla, ver la asistencia creada, registrar una justificación con archivo adjunto, descargarlo, y aprobarlo viendo cómo la asistencia cambia a "justificado" — todo contra un servidor real, con JWT real, antes de comprometer el código.

## Siguiente

Fase 7 — Notas (RF-17 a RF-20, RF-23, RF-10, RN-01 a RN-07). La fase más sensible del proyecto según el prompt maestro: tope de 100 puntos, punteo real que nunca se sobreescribe, plantillas de calificación, y modificaciones que solo Dirección autoriza.
