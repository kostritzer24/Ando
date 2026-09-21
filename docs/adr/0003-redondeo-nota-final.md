# ADR-0003: Redondeo de la nota final y regla flexible de pruebas cortas (RN-02 y RN-04 revisadas)

**Fecha:** 2026-09-20 (confirmado 2026-09-20)
**Estado:** Aceptado — redondeo aritmético estándar confirmado por dirección

## Contexto

RN-02 dice que la nota final es el promedio de las cuatro unidades "redondeado sin decimales", sin especificar el método. RN-04 dice "cuatro pruebas cortas de 10 puntos" como si fuera un valor fijo.

Al confirmar en Fase 0 (pregunta 10), la dirección aclaró que RN-04 no es un valor fijo: *"No, va variando, a veces son más pruebas cortas, pero mínimo son 4, depende del catedrático."* Esto cambia la regla de "siempre 4 pruebas de 10 puntos = 40 puntos fijos" a "mínimo 4 actividades marcadas como prueba corta, con la distribución de puntos a discreción del docente, siempre que el total de la unidad sume 100".

## Opciones consideradas para el redondeo (RN-02)

1. **Redondeo aritmético estándar** (0.5 hacia arriba): 79.5 → 80, 79.4 → 79.
2. **Redondeo bancario** (`round half to even`): 79.5 → 80, 78.5 → 78. Menos intuitivo para el personal no técnico que revisa boletines a mano.
3. **Truncamiento**: 79.9 → 79. Perjudica sistemáticamente al estudiante y no es lo que la mayoría de instituciones guatemaltecas usa en boletines.

## Decisión

- **Redondeo aritmético estándar** (mitad hacia arriba) para la nota final del ciclo, por ser el método que un docente o un padre de familia espera sin explicación adicional. Se implementa como una única función pura en `grading/domain/` (`calcular_nota_final`), sin lógica duplicada en ningún otro módulo (boletín, reporte, portal público, cálculo de puntos faltantes).
- **RN-04 se implementa como regla flexible, no fija:** una Actividad tiene un indicador `es_prueba_corta` (derivado de su `ActivityType`). El dominio valida, por unidad y asignación, que exista un **mínimo de 4** actividades con `es_prueba_corta = true`, y que la suma de `max_score` de **todas** las actividades de esa unidad y asignación sea exactamente 100 (RN-01/RN-02). No se exige que cada prueba corta valga exactamente 10 puntos ni que sean exactamente 4.

## Consecuencias

- El límite de 100 puntos por unidad y el mínimo de 4 pruebas cortas se validan en la capa de dominio al crear o modificar una Actividad, no solo en el formulario del frontend.
- `docs/trazabilidad.md` debe enlazar esta regla revisada con su prueba unitaria (`test_rn02_redondeo_...`, `test_rn04_minimo_pruebas_cortas_...`).
