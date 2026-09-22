# Fase 7 — Notas: cierre

Cubre RF-17 a RF-20, RF-23, RF-10, RN-01 a RN-07 (sección 18 del prompt maestro) — la fase que el propio prompt maestro señala como la más sensible del proyecto. Backend completo y probado; frontend pendiente (misma decisión de secuencia — ver `docs/pendiente-frontend.md`).

## Qué se construyó

- **`grading`:** `Activity`, `Grade`, `GradeChangeRequest`.
- **RN-01/RN-02/RN-04 (ADR-0003) en código:** una unidad no puede pasar de 100 puntos (validado actividad por actividad, no solo al final); una unidad "completa" exige el tope exacto de 100 y al menos 4 actividades marcadas como prueba corta — probado en ambos sentidos.
- **RN-02/RN-03 (ADR-0003) en código:** una sola función (`grading/domain/scoring.py`) calcula la nota final con redondeo aritmético estándar — confirmado con los tres casos límite (.25, .5, .75) — y decide si un curso se aprueba (60 puntos). Es la única función que hace este cálculo en todo el proyecto, para que boletín, reportes y portal público no puedan desalinearse entre sí más adelante.
- **RN-05 en código, no solo en el modelo:** `Grade.raw_score` nunca se sobreescribe. Intentar calificar dos veces la misma actividad para la misma inscripción se rechaza con un mensaje que señala el camino correcto (`/grade-change-requests/`), verificado en vivo.
- **RN-06 en código:** la API nunca expone `raw_score`, en ningún serializer, para ningún rol. La nota que se ve siempre es `current_score`. Probado explícitamente, no solo por omisión.
- **RN-07 en código:** volver a subir la plantilla de calificaciones para una actividad ya calificada no sobreescribe — crea una `GradeChangeRequest` automáticamente. Si el valor recargado es idéntico al vigente, no genera nada (ni una solicitud vacía). Verificado en vivo: calificar manualmente, recargar la plantilla con otro valor, ver la solicitud de modificación aparecer, aprobarla como Dirección y confirmar que `raw_score` sigue intacto mientras `current_score` cambia.
- **ADR-0001 aplicada de nuevo:** no se pueden definir actividades sobre una asignación de un curso de tipo taller — coherente con que los talleres solo generan asistencia, nunca notas.
- **Plantilla de calificaciones (RF-19/RF-20) con vista previa real de dos pasos**, a diferencia de la de asistencia (Fase 6, un solo paso): `POST /grades/template/preview/` clasifica cada celda como "crear", "modificación" o "sin cambio" sin guardar nada; `POST /grades/template/upload/` hace la misma validación y, si no hay errores, la aplica.
- **Autorización más fina que el área declarada, aplicada por segunda vez** (ya se había hecho en la Fase 5 para las asignaciones docentes): "solicitar" una modificación de nota vive en el área `notas` (footnote 7 de `docs/permisos-roles.md`), pero "aprobar/rechazar" vive en el área separada `modificacion_notas`, exclusiva de Dirección — una sola vista (`GradeChangeRequestViewSet`) cambia de área según la acción.

**Verificación real:** 207 pruebas (53 nuevas), 97 % de cobertura en `domain/`+`services/`, y un flujo completo en vivo contra un servidor real — diseñar una unidad hasta los 100 puntos exactos (con un intento de pasarse rechazado en el camino), calificar, intentar calificar dos veces, descargar la plantilla, cargarla, recargarla con un valor distinto para generar una solicitud de modificación, aprobarla como Dirección, y confirmar que el punteo real nunca cambió — todo con JWT real, antes de comprometer el código.

## Ajuste menor sobre la marcha

Al escribir varias pruebas que necesitaban dos usuarios con el mismo rol ("Docente") en la misma prueba, apareció un choque con la restricción `unique=True` de `Role.name` — cada prueba intentaba crear una fila de rol nueva en vez de reutilizar la existente. Se corrigió agregando `django_get_or_create = ("name",)` a `RoleFactory` (`apps/accounts/tests/factories.py`): dentro de una misma prueba, pedir el mismo nombre de rol ahora reutiliza la fila, tal como pasa en producción (el rol es uno solo; lo que varía es el usuario).

## Siguiente

Fase 8 — Horarios y calendario (RF-06, RF-22, RF-26, RN-13, RN-17). `ScheduleBlock` y `CalendarEvent`, los dos modelos de `scheduling` que todavía faltaban.
