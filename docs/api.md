# Contrato de la API — planeación

Este documento es el contrato **de planeación** para la Fase 1: fija qué endpoints existen, con qué propósito y qué RF cubren, antes de escribir una sola vista. Una vez empiece la implementación (Fase 3 en adelante), la fuente de verdad pasa a ser el esquema OpenAPI generado automáticamente por Django REST Framework (sección 12.3 del prompt maestro) y este archivo se actualiza para reflejarlo, no al revés.

Todo bajo el prefijo `/api/v1/`. Los roles se listan con los códigos de `docs/permisos-roles.md` (DIR, COORD, PAGOS, DOC, GUÍA, TALL, FAM, ADMIN); "según matriz" significa que el alcance de objeto de esa matriz aplica sin excepción.

## `accounts` — Usuarios y autenticación

| Método | Ruta | Propósito | RF / sección | Roles |
|---|---|---|---|---|
| POST | `/auth/login/` | Iniciar sesión, emite token de acceso y refresco | RF-27, 14.1 | público (con credenciales) |
| POST | `/auth/refresh/` | Rotar token de acceso desde la cookie de refresco | 14.1 | autenticado |
| POST | `/auth/logout/` | Revocar el token de refresco actual | 14.1 | autenticado |
| POST | `/auth/change-password/` | Cambio obligatorio de contraseña temporal | 14.1 | autenticado |
| GET | `/auth/me/` | Perfil propio — reconstruye la sesión en el frontend tras recargar la página, sin pasar por `/users/{id}/` (exclusiva de Dirección/Administrador) | 14.1, agregada en el bloque de frontend | cualquier autenticado, sobre sí mismo |
| GET, POST | `/users/` | Listar / crear usuarios con su rol | RF-01 | DIR, ADMIN (E) |
| GET, PATCH | `/users/{id}/` | Ver / editar un usuario | RF-01 | DIR, ADMIN (E) |
| POST | `/users/{id}/reset-password/` | Restablecer contraseña gestionado por administración (no por correo) | RF-01, 14.1 | DIR, ADMIN (E) |
| GET | `/roles/` | Listar roles y sus permisos por área | RNF-03 | DIR, ADMIN (V/E) |

## `catalog` — Datos maestros

CRUD estándar (`GET` lista/detalle, `POST` crea, `PATCH` edita, `DELETE` da de baja lógica — nunca borra) sobre cada uno de los siete catálogos de la sección 9, más el octavo catálogo agregado por ADR-0006:

| Recurso | Ruta base | RF |
|---|---|---|
| Ciclos escolares | `/cycles/` | RF-02 |
| Unidades | `/cycles/{cycle_id}/units/` | RF-02 |
| Secciones | `/sections/` | RF-02 |
| Cursos | `/courses/` | RF-02 |
| Tipos de actividad | `/activity-types/` | RF-02 |
| Tipos de justificación | `/justification-types/` | RF-02 |
| Tipos de documento | `/document-types/` | RF-02 |
| Becas | `/scholarships/` | RF-02 |
| Artículos del código de convivencia | `/conduct-rule-articles/` | ADR-0006 |

Roles: DIR, ADMIN (E); COORD (V); el resto sin acceso, según matriz — **con tres excepciones**, todas del mismo tipo (un rol operativo necesita leer una opción para poder usarla, aunque no administre el catálogo): la lectura (`GET`) de `/justification-types/` pasa por el área "asistencia" (RF-12 — docente, guía, tallerista eligen tipo de justificación); la de `/activity-types/` y `/cycles/{cycle_id}/units/` pasa por el área "notas" (RF-17 — docente/guía eligen tipo de actividad y unidad al diseñarla). Administrar cualquiera de los tres catálogos (crear/editar/dar de baja) sigue siendo exclusivo de "datos_maestros", igual que los otros cinco.

## `students` — Estudiantes, encargados e inscripción

| Método | Ruta | Propósito | RF / HU | Roles |
|---|---|---|---|---|
| GET, POST | `/students/` | Listar / inscribir estudiantes | RF-03, HU-03 | DIR (E), COORD/PAGOS/DOC/GUÍA/TALL (V, según matriz) |
| GET, PATCH | `/students/{id}/` | Ver / editar expediente general | RF-03 | según matriz |
| GET | `/students/{id}/sensitive/` | Datos de salud y socioeconómicos, serializer aparte | RNF-04 | DIR (V/E), ADMIN (V, queda en `AccessLog`) |
| GET, POST | `/guardians/` | Listar / crear encargados | RF-03 | DIR (E) |
| GET, POST | `/guardians/{id}/link-student/` | Consultar / vincular encargado con estudiante (`GuardianStudentLink`) | RF-04 | DIR (E) |
| DELETE | `/guardians/{id}/link-student/{student_id}/` | Retirar vínculo (baja lógica) | RF-04 | DIR (E) |
| GET | `/me/students/` | Estudiantes vinculados al encargado autenticado, para el selector | HU-27 | FAM (V, propio) |
| GET, POST | `/enrollments/` | Inscripciones por ciclo/sección | RF-03 | DIR (E) |

## `scheduling` — Asignaciones, horarios y calendario

| Método | Ruta | Propósito | RF / HU | Roles |
|---|---|---|---|---|
| GET, POST | `/assignments/` | Asignar docente/tallerista a curso-sección, maestro guía a sección | RF-05 | DIR (E) |

`TeacherAssignmentSerializer` incluye `section_grade`, `section_letter`, `section_type` y `course_name` de solo lectura — un docente no llega a `/sections/` ni `/courses/` (área "datos_maestros", sección S para su rol), pero sí necesita saber el grado y el curso de su propia asignación para las pantallas operativas (asistencia, y más adelante notas). Se expone acá en vez de abrirle el catálogo completo.
| GET, POST | `/schedule-blocks/` | Armar horario; rechaza cruces de docente y período | RF-06, HU-06 | DIR (E) |
| GET | `/schedule/mine/` | Horario propio del docente autenticado | RF-26 | DOC, GUÍA, TALL (V, propio) |
| GET, POST | `/calendar-events/` | Publicar asignaciones/eventos en el calendario | RF-22 | DOC, GUÍA (E, solo lo publicado); DIR (E, todo) |
| GET | `/calendar/weekly/` | Calendario semanal del estudiante seleccionado — pantalla de entrada del portal público | RF-28, RF-32 | FAM (V, propio) |

## `attendance` — Asistencia y justificaciones

| Método | Ruta | Propósito | RF / RN | Roles |
|---|---|---|---|---|
| GET, POST | `/attendance/` | Registrar / consultar asistencia diaria (jornada matutina y talleres) | RF-16, RN-11 | DOC, GUÍA, TALL (E, propio); DIR (E, todo) |
| GET | `/attendance/template/{section_id}/{date}/` | Generar plantilla de asistencia de talleres | RF-21 | TALL, DIR (E) |
| POST | `/attendance/template/upload/` | Cargar plantilla con validación y vista previa | RF-21 | TALL, DIR (E) |
| GET, POST | `/justifications/` | Registrar justificación de falta | RF-12 | DOC, GUÍA, DIR (E) |
| POST | `/justifications/{id}/resolve/` | Aprobar/rechazar justificación | RF-12, RN-12 | DIR (E) |

## `grading` — Actividades, calificaciones y boletines

| Método | Ruta | Propósito | RF / RN | Roles |
|---|---|---|---|---|
| GET, POST | `/activities/` | Definir actividades evaluativas de una unidad | RF-17, RN-01/02/04 | DOC, GUÍA (E, propio) |
| POST | `/grades/` | Registrar punteo real de una actividad | RF-18 | DOC, GUÍA (E, propio) |
| GET | `/grades/template/{assignment_id}/{unit_id}/` | Generar plantilla de calificaciones | RF-19 | DOC, GUÍA (E, propio) |
| POST | `/grades/template/preview/` | Vista previa fila por fila antes de guardar (HU-19/20) | RF-20 | DOC, GUÍA |
| POST | `/grades/template/upload/` | Confirmar carga de la plantilla ya validada | RF-20, RN-07 | DOC, GUÍA |
| GET | `/grades/missing-points/{enrollment_id}/` | Puntos faltantes para aprobar, por curso | RF-30, HU-30 | FAM (V, propio); DOC/GUÍA (V, propio) |
| POST | `/grade-change-requests/` | Solicitar corrección de una nota | RF-23 | DOC, GUÍA (E) |
| POST | `/grade-change-requests/{id}/approve/` | Autorizar modificación | RF-10, RN-05 | solo DIR |
| POST | `/grade-change-requests/{id}/reject/` | Rechazar modificación | RF-10 | solo DIR |
| POST | `/report-cards/generate/` | Generar boletín de una sección/unidad | RF-09 | DIR (E) |
| POST | `/report-cards/{id}/approve/` | Aprobar boletín | RF-09 | DIR (E) |
| POST | `/report-cards/{id}/publish/` | Publicar boletín (sujeto a RN-09/RN-10) | RF-09 | DIR (E) |
| GET | `/report-cards/{id}/download/` | Descargar boletín, enlace firmado de corta duración | RF-34 | FAM (V, propio, solo si habilitado) |

## `payments` — Pagos, solvencia y constancias

| Método | Ruta | Propósito | RF / RN | Roles |
|---|---|---|---|---|
| GET, POST | `/payments/` | Registrar / consultar pagos mensuales | RF-07 | PAGOS, DIR (E) |
| GET | `/solvency/{enrollment_id}/` | Estado de solvencia calculado (incluye beca, RN-08) | RF-07, RF-33 | PAGOS, DIR (V/E); FAM (V, propio) |
| POST | `/solvency/{enrollment_id}/certificate/` | Emitir constancia de solvencia en PDF | RF-08 | PAGOS, DIR (E) |

## `documents` — Documentos emitidos y verificación

| Método | Ruta | Propósito | RF / HU | Roles |
|---|---|---|---|---|
| POST | `/documents/issue/` | Emitir constancia de estudio/conducta o carta membretada | RF-11 | DIR (E) |
| GET | `/documents/{id}/download/` | Descargar documento emitido, enlace firmado | RF-11 | según documento |
| GET | `/verify/{verification_code}/` | Verificación pública: tipo, fecha, estudiante — sin datos sensibles | RF-14, HU-14 | **público, sin sesión, con límite de tasa** |

## `communication` — Avisos, conducta y buzón

| Método | Ruta | Propósito | RF / HU | Roles |
|---|---|---|---|---|
| GET, POST | `/announcements/` | Publicar / listar avisos de cartelera | RF-13, HU-36 | DIR (E); resto (V) |
| GET, POST | `/conduct-reports/` | Registrar reportes de conducta | RF-24 | GUÍA, DIR (E) |
| GET, POST | `/messages/` | Enviar mensaje al buzón / listar hilos propios | RF-25, RF-37, HU-25 | FAM (E, propio); GUÍA, DIR (E, su sección) |
| POST | `/messages/{id}/reply/` | Responder dentro del mismo hilo | RF-25 | GUÍA, DIR |

## `reports` — Consultas institucionales

Todas aceptan `?cycle=&unit=&section=&format=pdf`.

| Ruta | Reporte | RF |
|---|---|---|
| `/reports/grades-summary/` | Consolidado de notas | RF-15 |
| `/reports/attendance/` | Asistencia | RF-15 |
| `/reports/insolvent-students/` | Estudiantes insolventes | RF-15 |
| `/reports/schedules/` | Horarios | RF-15 |
| `/reports/enrolled-students/` | Estudiantes inscritos | RF-15 |
| `/reports/grade-change-history/` | Historial de modificaciones de notas | RF-15 |
| `/reports/family-access/` | Accesos de las familias | RF-15, RNF-07 |
| `/reports/issued-documents/` | Documentos emitidos | RF-15, RNF-07 |
| `/reports/metrics/` | Métricas del estudio (sin datos personales) | sección 11 |

Roles: DIR, ADMIN (V); COORD (V); el resto sin acceso, según matriz.

## `core` — Transversal

| Método | Ruta | Propósito | Roles |
|---|---|---|---|
| GET | `/audit-log/?entity=&entity_id=` | Consultar bitácora de cambios | DIR, ADMIN (V) |
| GET | `/access-log/?user=` | Consultar registro de accesos | DIR, ADMIN (V) |

## Notas de diseño del contrato

- Ningún endpoint de escritura queda sin una clase de permiso explícita (sección 14.2): la clase base de `core/` niega por defecto.
- Las descargas de PDF (`/report-cards/{id}/download/`, `/documents/{id}/download/`, constancias) van siempre detrás de autenticación y devuelven una URL firmada de corta duración, nunca el archivo directo desde una carpeta pública.
- `/verify/{verification_code}/` es la única ruta sin sesión en todo el contrato (RF-14); lleva límite de tasa dedicado.
- Los endpoints de plantilla (`/grades/template/...`, `/attendance/template/...`) siempre separan `preview` de `upload` confirmado, para cumplir HU-19/20 (vista previa fila por fila antes de guardar).
