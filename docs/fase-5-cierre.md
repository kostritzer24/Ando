# Fase 5 — Expedientes y asignaciones: cierre

Cubre RF-03, RF-04, RF-05 (sección 18 del prompt maestro). Backend completo y probado; frontend pendiente (misma decisión de secuencia que la Fase 4 — ver `docs/pendiente-frontend.md`).

## Qué se construyó

- **`students`:** `Student`, `Guardian`, `GuardianStudentLink`, `Enrollment`.
- **`scheduling`:** `TeacherAssignment` (primer modelo real de esta app; `ScheduleBlock`/`CalendarEvent` llegan en la Fase 8).
- **RN-14 en código:** el código interno del estudiante (`ES` + 3 dígitos) lo genera siempre el sistema (`students/domain/internal_code.py`); el cliente nunca puede fijarlo, probado explícitamente.
- **HU-03 en código:** un estudiante no puede quedar inscrito dos veces en el mismo ciclo — validado en el servicio con un mensaje claro, además de la restricción de base de datos.
- **ADR-0002 en código:** un estudiante puede tener más de un encargado vinculado, cada vínculo con su propio parentesco (`GuardianStudentLink`), probado con el caso de dos encargados distintos para el mismo estudiante.
- **RNF-04 en código, no solo en la matriz:** `Student` tiene un serializer general que **nunca** incluye `health_notes`/`socioeconomic_notes`; esos datos solo se sirven desde `/students/{id}/sensitive/`, con su propio permiso de área (`datos_sensibles`), distinto del que rige el resto del expediente (`estudiantes_encargados`). Se probó que Dirección edita, Administrador solo ve, y el resto (incluida la propia familia del estudiante) no alcanza ni a ver esa ruta.
- **Alcance por objeto (RNF-04) para tres roles distintos**, todos ejercidos contra el mismo endpoint `/students/`:
  - Padre de familia ve solo a los estudiantes vinculados a su cuenta.
  - Docente/Docente con sección a cargo/Tallerista ven solo a los estudiantes inscritos en secciones donde tienen una asignación vigente.
  - Dirección, Coordinación, Encargado de pagos y Administrador ven todo, según su nivel en la matriz.
- **ADR-0001 extendida a la asignación docente (RF-05):** `scheduling/domain/teacher_assignment.py` rechaza una asignación si el tipo de curso no coincide con el tipo de sección, **y además** si el rol de quien se asigna no corresponde (un tallerista no puede quedar asignado a un curso académico, ni un docente a un taller).
- **Corrección sobre la Fase 4:** el maestro guía de una `Section` ahora también valida que el usuario tenga el rol "Docente con sección a cargo" (antes solo se validaba que la sección fuera académica) — se detectó al construir la asignación docente de esta fase y se corrigió con su propia prueba.
- **Permiso más fino que el área declarada:** `/assignments/` (crear/editar/eliminar) queda reservado a Dirección exclusivamente, aunque el área `horarios_calendario` le da "editar" también a docentes y talleristas para su propio horario (Fase 8) — se implementó un permiso adicional (`_SoloDireccionCreaAsignaciones`) para no confundir "editar mi horario" con "decidir quién da qué curso", conforme a `docs/api.md`.
- **`manage.py seed_demo` se mudó de `catalog` a `core`** (ahora toca varias apps) y se extendió con 4 estudiantes inscritos, 1 encargada vinculada y 2 asignaciones docentes — verificado en vivo, incluida la idempotencia (correrlo dos veces no duplica nada).

**Verificación real:** 119 pruebas (39 nuevas), 98 % de cobertura en `domain/`+`services/`, y una corrida en vivo completa: crear estudiante → inscribir → crear encargado → vincular → asignar docente → confirmar que la cuenta familiar ve solo a su estudiante — contra un servidor real, con JWT real, antes de comprometer el código.

## Siguiente

Fase 6 — Asistencia (RF-16, RF-12, RF-21, RN-11, RN-12). Backend, siguiendo la misma decisión de secuencia (frontend en bloque aparte).
