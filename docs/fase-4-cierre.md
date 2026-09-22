# Fase 4 — Datos maestros: cierre

Cubre RF-02 (sección 18 del prompt maestro). Backend completo y probado; frontend pendiente por decisión explícita (ver abajo).

## Qué se construyó

- **9 catálogos** (los 7 de la sección 9 + Beca, que también aparece ahí, + `ConductRuleArticle` de ADR-0006): `SchoolCycle`, `GradingUnit`, `Section`, `Course`, `ActivityType`, `JustificationType`, `DocumentType`, `Scholarship`, `ConductRuleArticle`.
- **`core.BaseModel`** nuevo (abstracto): centraliza `public_id`/`is_active`/`created_at`/`updated_at` para que cada modelo de negocio futuro no repita esas cuatro columnas.
- **`core.BajaLogicaMixin`** nuevo: `DELETE` dado de baja lógica en vez de borrar (HU-02), reutilizable en cualquier ViewSet futuro.
- **RN-10 aplicada en código, no solo en documentación:** `GradingUnit.grades_due_date` y `.report_card_enabled_date` se calculan siempre a partir de `end_date` (`catalog/domain/grading_unit.py`); el cliente nunca puede forzar esas fechas, probado explícitamente.
- **ADR-0001 aplicada en código:** una `Section` de tipo `taller` con `homeroom_teacher` es rechazada por la API con 400, tanto al crear como al editar (`catalog/domain/section.py`).
- **Permisos:** los 9 recursos usan el área `datos_maestros` de `docs/permisos-roles.md` (Dirección/Administrador editan, Coordinación ve, el resto sin acceso).
- **`manage.py seed_demo`:** nuevo comando que encadena `seed_fase3` y agrega un ciclo 2026 con sus 4 unidades, las 6 secciones de la jornada matutina más una de taller, cursos, los 4 catálogos restantes, y los 16 artículos reales del código de convivencia de `docs/reporte.docx`. Es el comando que se sigue extendiendo fase a fase — no se crea uno nuevo por cada fase.

**Verificación real:** 80 pruebas (35 nuevas), 100 % de cobertura en `domain/`+`services/`, y una corrida en vivo contra un servidor real (login, listar unidades con fechas calculadas, listar secciones, listar los 16 artículos) antes de comprometer el código.

## Decisión de alcance

RF-02 ("Administrar los datos maestros del centro") es una capacidad que se usa desde el portal, así que estrictamente incluye pantallas de frontend, no solo la API. Se le preguntó al equipo cómo secuenciar el resto del trabajo y se decidió: **backend primero en cada fase, frontend de negocio en un bloque aparte más adelante.** La Fase 3 (login) es la única excepción, porque su frontend era indispensable para poder probar cualquier otra cosa.

Lo que queda pendiente de esta fase para esa pasada de frontend está en `docs/pendiente-frontend.md`, para no tener que reconstruir el contexto desde el historial de commits cuando llegue el momento.

## Siguiente

Fase 5 — Expedientes y asignaciones (RF-03, RF-04, RF-05): Estudiante, Encargado, `GuardianStudentLink`, Inscripción, Asignación docente y maestro guía. Backend, siguiendo la misma decisión de secuencia.
