# ADR-0001: Los talleres se modelan con Sección e Inscripción, igual que la jornada matutina

**Fecha:** 2026-09-20
**Estado:** Aceptado

## Contexto

Las 25 entidades del Capítulo IV no distinguen explícitamente una tabla para "participante de taller" frente a "estudiante inscrito en la jornada matutina". Curso tiene un atributo `tipo` y Sección tiene `grado, letra, tipo`, pero no queda escrito si un taller de la tarde usa Sección/Inscripción o un mecanismo aparte.

Se preguntó directamente (Fase 0, pregunta 1) y la dirección confirmó: *"Los talleres de la tarde sí tienen sección también porque muchas veces son por grupos y en algunos casos son pues un solo grupo que sería sección única."*

## Opciones consideradas

1. **Reusar Sección e Inscripción para talleres**, agregando `Section.type = 'taller'` junto a `'academica'`. Un taller con un solo grupo se modela como una sección con un único registro.
2. **Crear una entidad paralela** ("Grupo de taller" / "Participante de taller") separada de Sección e Inscripción, con su propio ciclo de vida.

La opción 2 duplica el concepto de "conjunto de estudiantes que comparten curso y horario" que ya resuelve Sección, y obligaría a duplicar también Asistencia, Asignación docente y Bloque de horario para talleres. La opción 1 es la que confirmó la dirección y además es la que menos entidades nuevas agrega.

## Decisión

Se usa **Sección** con `type` en `{'academica', 'taller'}` y **Inscripción** sin cambios para ambos casos. Un Curso también lleva `type` en `{'academico', 'taller'}`, y una Asignación docente solo es válida si `Course.type == Section.type` (regla de dominio, no solo de interfaz).

Consecuencia directa: **Actividad y Calificación solo se pueden crear sobre una Asignación docente cuyo Course.type sea `'academico'`** — ver ADR relacionado en la sección de reglas de dominio de `docs/modelo-datos.md` (confirmado en la pregunta 3 de la Fase 0: "Es solo asistencia").

## Consecuencias

- No se agrega ninguna entidad nueva para talleres; Asistencia, Sección, Inscripción y Asignación docente se comparten entre jornada matutina y talleres.
- El dominio debe impedir la creación de Actividad/Calificación cuando la Asignación docente apunta a un Curso de tipo `'taller'`.
- El maestro guía (`Section.homeroom_teacher`) solo aplica a secciones de tipo `'academica'`; una sección de taller no lleva maestro guía.
- Los reportes que filtran "por sección" deben distinguir tipo de sección para no mezclar, por ejemplo, el consolidado de notas (que no aplica a talleres) con el de asistencia (que sí aplica a ambos).
