# Fase 5 (frontend) — Expedientes y asignaciones: cierre

Segunda fase del bloque de frontend. Cubre RF-03, RF-04, RF-05: expedientes de estudiantes, encargados y sus vínculos, y asignación de docentes/talleristas a curso-sección.

## Qué se construyó

- **`EstudiantesPage.vue`**: lista de estudiantes + "Inscribir estudiante", que en un solo formulario crea el `Student` (`POST /students/`) y de una vez la `Enrollment` en la sección elegida (`POST /enrollments/`) — el código interno nunca se pide, se muestra recién generado al terminar.
- **`ExpedientePage.vue`**: datos generales editables solo por Dirección (`docs/permisos-roles.md`: esta área da `E` únicamente a Dirección, ni Administrador edita acá) y la sección de "Datos sensibles" con tres alcances distintos — Dirección edita, Administrador solo consulta, el resto de roles ni siquiera dispara la petición a `/students/{id}/sensitive/`.
- **`EncargadosPage.vue`**: alta de encargados y gestión de vínculos con estudiantes (vincular/desvincular), con la lista de vínculos ya existentes visible antes de tocar nada.
- **`AsignacionesPage.vue`**: asignar docente/tallerista a curso-sección con el curso y la persona filtrados según el tipo de la sección elegida (ADR-0001) — académica solo ofrece cursos académicos y personas con rol Docente/Docente con sección a cargo; taller solo ofrece cursos de taller y Talleristas. Evita en la interfaz combinaciones que el backend rechazaría de todas formas.
- Coordinación (y cualquier otro rol que llegue a estas pantallas) ve todo de solo lectura — mismo patrón de esconder los botones de escritura que en la Fase 4, esta vez con Dirección como único rol habilitado en vez de "cualquiera menos Coordinación" (la matriz de esta área es más estricta).

## Bug real encontrado y corregido: `GET /enrollments/` no tenía alcance por objeto

Al armar el expediente del estudiante, `EnrollmentSerializer` reveló que `EnrollmentViewSet` no heredaba de `ScopedQuerysetMixin` — a diferencia de `StudentViewSet`, que sí lo hace sobre la misma área (`estudiantes_encargados`). El efecto real: cualquier cuenta con `ver` en esa área —lo que incluye a una familia (`Padre de familia` tiene `V ³`, limitado por diseño a sus propios estudiantes)— podía listar la inscripción de **cualquier** estudiante del centro, con su sección, ciclo y si tiene beca o no. Se corrigió agregando el mismo criterio de alcance que ya usa `StudentViewSet`: sin límite para Dirección/Coordinación/Pagos/Administrador, propio para familias (por vínculo activo) y por sección asignada para docentes/talleristas. Se agregaron dos pruebas de regresión (`apps/students/tests/test_rnf04_aislamiento_inscripciones_por_rol.py`).

## Bug real encontrado y corregido: no existía forma de consultar los vínculos de un encargado

`docs/pendiente-frontend.md` pedía "la lista de vínculos existentes" en la pantalla de encargados, pero el backend solo exponía `POST` (crear vínculo) y `DELETE` (desvincular) — ningún `GET`. Se agregó como el mismo endpoint (`GET /guardians/{id}/link-student/`), con un serializer de lectura aparte (`GuardianStudentLinkReadSerializer`) que sí incluye el nombre y código del estudiante para mostrarlo, cosa que el serializer de escritura no necesita. De paso, el primer intento de documentar el endpoint con `@extend_schema` generó un esquema que decía que la respuesta venía paginada (`{count, next, previous, results}`) cuando en realidad la vista nunca pagina esta lista — se corrigió con `pagination_class=None` en la acción, para que el contrato generado coincida con lo que el backend de verdad devuelve.

## Verificación real

12 pruebas nuevas de backend (2 de alcance de inscripciones, 1 de la nueva consulta de vínculos, más las que ya cubrían el resto de RF-03/RF-04) y 6 pruebas de extremo a punta contra un navegador real: inscribir un estudiante y ver el código generado, ver y editar el expediente general y los datos sensibles como Dirección, confirmar que Coordinación ve el expediente sin poder editarlo ni ver datos sensibles, crear un encargado (usuario + perfil en un solo flujo) y vincularlo/desvincularlo de un estudiante, y asignar un docente a una sección académica confirmando que el selector de personas excluye a los talleristas — y viceversa para una sección de taller. `vue-tsc --noEmit` y `eslint` sin errores; 284 pruebas de backend en verde.

## Siguiente

Fase 6 (frontend) — Asistencia: registro diario por sección, justificaciones (crear y resolver), plantilla de asistencia para talleres. Detalle completo en `docs/pendiente-frontend.md`.
