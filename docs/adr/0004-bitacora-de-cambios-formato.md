# ADR-0004: La bitácora de cambios guarda el valor anterior y nuevo como JSON, no como columnas tipadas

**Fecha:** 2026-09-20
**Estado:** Aceptado

## Contexto

RNF-06 exige una bitácora de cambios en notas, pagos y asistencia con usuario, entidad afectada, valor anterior, valor nuevo y fecha. Esa bitácora debe cubrir entidades de forma heterogénea (una Calificación, un Pago, una Asistencia — cada una con columnas distintas).

## Opciones consideradas

1. **Una tabla de bitácora por entidad auditada** (`grading_auditlog`, `payments_auditlog`, `attendance_auditlog`), cada una con columnas tipadas iguales a la entidad que audita.
2. **Una sola tabla `AuditLog`** con `entity_name`, `entity_id`, `old_value` y `new_value` como campos JSON, más `action` y `user`.

La opción 1 obliga a triplicar el modelo y a tocar tres lugares cada vez que se agregue trazabilidad a una nueva entidad (por ejemplo, si más adelante se decide auditar Enrollment). La opción 2 centraliza la bitácora en `core/`, que es donde vive lo transversal según la arquitectura por capas (sección 12.1 del prompt maestro).

## Decisión

Una sola tabla `core.AuditLog`, de solo escritura (sin `updated_at`, sin baja lógica: un registro de bitácora nunca se modifica ni se borra). `old_value` y `new_value` se guardan como JSON con los campos relevantes de la entidad en el momento del cambio, no el objeto completo. Se escribe siempre desde la capa de servicios (`services/`), dentro de la misma transacción que el cambio que audita — nunca desde una señal (`signal`) de Django, para que quede explícito en el caso de uso qué se está auditando y con qué motivo.

## Consecuencias

- Toda consulta de "historial de modificaciones de notas" (reporte 6 de la sección 11) filtra `AuditLog` por `entity_name = 'grading.Grade'`.
- Se agregan índices sobre `(entity_name, entity_id, created_at)` y `(user_id, created_at)` desde la primera migración, por el riesgo de crecimiento indefinido ya señalado en la Fase 0 (riesgo 9).
- La modificación de nota (RN-05) usa además su propia tabla `GradeChangeRequest` para el flujo de autorización — la bitácora registra el resultado final una vez aprobado, no sustituye ese flujo.
