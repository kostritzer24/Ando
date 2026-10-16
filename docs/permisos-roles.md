# Matriz de roles contra permisos por área

RNF-03 exige tres niveles por área: **V** (ver), **E** (editar, incluye crear/actualizar dentro de su alcance) y **S** (sin acceso). Esta matriz es la base para las clases de permiso de `core/` (sección 14.2 del prompt maestro): la clase base niega y cada rol concede explícitamente.

**Importante:** varias celdas se infieren de las descripciones de actor de la sección 2 y de a qué portal pertenece cada RF, porque el Capítulo IV no entrega una matriz de permisos ya armada. Donde la inferencia no es directa, se marca `¿?` y queda listado al final como pregunta para dirección — conforme a la regla de trabajo 3 (no completar en silencio).

`E` **siempre implica alcance limitado a nivel de objeto** (sección 14.2): un docente con `E` en Notas solo edita las asignaciones que tiene asignadas, un docente con `E` en Buzón solo ve los hilos de las secciones donde da clase o figura como docente a cargo, un encargado con `V` en Notas solo ve a sus estudiantes vinculados. La matriz no repite esa condición en cada celda para no saturarla; se aplica siempre.

## Roles

Dirección (DIR), Coordinación (COORD), Encargado de pagos (PAGOS), Docente (DOC), Tallerista (TALL), Padre de familia (FAM).

> **Cambio de la ronda de pruebas (oct. 2026):** desaparecen los roles «Docente con sección a cargo» (maestro guía) y «Administrador del sistema». Cualquier docente puede ser el docente a cargo de una sección y levantar reportes de conducta o responder el buzón en las secciones donde da clase; Dirección administra las cuentas. Quien tenía el primer rol pasó a Docente y quien tenía el segundo, a Coordinación (solo lectura), por una migración de datos.

## Matriz

| Área | DIR | COORD | PAGOS | DOC | TALL | FAM |
| --- | --- | --- | --- | --- | --- | --- |
| Usuarios y roles | E | S | S | S | S | S |
| Datos maestros (7 catálogos) | E | V | S | S | S | S |
| Estudiantes y encargados (datos generales) | E | V | V ¹ | V ² | V ² | V ³ |
| Datos sensibles (salud, socioeconómicos) | E | S | S | S | S | S |
| Horarios y calendario | E | V | S | E ² | E ² | V ³ |
| Asistencia | E ⁴ | V | S | V ² | E ² | V ³ |
| Notas (actividades, calificaciones, boletín) | E | V | S | E ² | S ⁵ | V ³ ⁶ |
| Modificación de notas (autorizar/rechazar) | E | S | S | S ⁷ | S | S |
| Pagos y solvencia | E | V | E | S | S | V ³ |
| Documentos emitidos | E | V | E ¹ | S | S | V ³ |
| Avisos (cartelera) | E | `¿?` | S | V | V | V |
| Reportes de conducta | E | `¿?` | S | E ² | S | V ³ |
| Buzón | E | S | S | E ² | S | E ³ |
| Reportes institucionales (RF-15) | E | V | S ⁸ | S | S | S |
| Bitácora y registro de acceso | V | S | S | S | S | S |

**Notas:**

1. `PAGOS` con `V`/`E` en Estudiantes y Documentos está limitado a lo necesario para facturar y emitir constancias de solvencia — no alcanza notas, asistencia ni datos sensibles.
2. `DOC` y `TALL` solo alcanzan las secciones/cursos de sus asignaciones vigentes (`TeacherAssignment`); `TALL` nunca alcanza Notas porque los talleres no califican (ADR-0001).
3. `FAM` con `V`/`E` está siempre limitado a los estudiantes vinculados a su cuenta (`GuardianStudentLink`, ADR-0002), nunca a estudiantes ajenos.
4. `DIR` registra asistencia matutina aunque el módulo pertenezca al portal operativo (sección 2 del prompt maestro, aclarado explícitamente).
5. `TALL` no tiene acceso a Notas de ningún tipo, ni siquiera de su propio taller, porque el taller no genera calificaciones.
6. `FAM` en Notas ve únicamente la nota final (`Grade.current_score`), nunca `GradeChangeRequest` (RN-06).
7. `DOC` tiene `E` en "solicitar modificación de nota" (RF-23) pero no en "autorizar" — son acciones distintas; la matriz separa ambas filas a propósito.
8. `PAGOS` no ve los reportes institucionales generales, solo el reporte de estudiantes insolventes, que en la práctica es una vista dentro de Pagos y solvencia, no de Reportes — **resuelto en la Fase 12** (`docs/fase-12-frontend-cierre.md`): ese reporte puntual vive en el área `pagos_solvencia`, con su propio botón en la pantalla de Pagos, en vez de en `reportes_institucionales`.
9. ~~`ADMIN` con `V` en datos sensibles~~ — el rol Administrador del sistema se eliminó en la ronda de pruebas de octubre de 2026; los datos sensibles quedan solo para `DIR`.

> **Cambio de la demostración al director (oct. 2026):** el Docente solo *consulta* la asistencia que marcó Dirección; ya no la marca. El Tallerista sí la marca, en sus talleres.

## Pendientes de confirmación con dirección

- **Coordinación:** la sección 2 dice que "acompaña a la dirección y firma informes de su comisión", pero no especifica sobre qué área tiene permiso de edición además de ver. Se dejó `V` por defecto en toda el área administrativa y `¿?` en Avisos y Reportes de conducta, que son los dos módulos donde "firmar un informe" podría implicar editar. **No se implementará ningún `E` para Coordinación hasta que se confirme.**
- ~~**Administrador del sistema y datos sensibles**~~ — el rol ya no existe.
- ~~**Pagos y solvencia — vista de reportes:** ver nota 8.~~ Resuelto en la Fase 12.

Las otras dos preguntas siguen abiertas desde el resumen de cierre de la Fase 1; ninguna fase posterior las tocó porque ninguna requería construir Avisos/Reportes de conducta para Coordinación ni acceso de Administrador a datos sensibles más allá de lo ya implementado.
