# Frontend pendiente

Desde la Fase 4 en adelante, el trabajo avanza backend primero por fase; el frontend de negocio se construye en un bloque aparte más adelante (decisión del equipo, ver `docs/fase-4-cierre.md`). Este documento lleva la cuenta de qué pantallas quedan debiendo cada fase, para que esa pasada de frontend no tenga que releer todo el histórico de commits.

La Fase 3 es la excepción: su frontend (login, cambio de contraseña, guards por rol) ya está construido — ver `docs/fase-3-cimientos-plan.md`.

## Pendiente

### Fase 4 — Datos maestros (RF-02)
Pantallas de administración de los 9 catálogos, portal administrativo, rol Dirección (editar) / Coordinación (ver):

- Ciclos escolares y sus unidades (con las fechas calculadas de solo lectura, RN-10)
- Secciones (con selector de maestro guía, deshabilitado si el tipo es "taller" — ADR-0001)
- Cursos
- Tipos de actividad evaluativa
- Tipos de justificación
- Tipos de documento
- Becas
- Artículos del código de convivencia

Contrato ya fijado en `docs/api.md`; los 9 recursos comparten el mismo patrón de lista + formulario + baja lógica, así que probablemente conviene una pantalla "genérica" de catálogo reutilizada 8 veces y una pantalla propia solo para Unidades (por la relación anidada con Ciclo) y Secciones (por el selector de maestro guía).

### Fase 5 — Expedientes y asignaciones (RF-03, RF-04, RF-05)
Portal administrativo, rol Dirección:

- Inscribir estudiante (formulario simple; el código interno lo muestra el sistema después de crear, nunca se pide)
- Expediente del estudiante: datos generales editables por Dirección/Coordinación; pestaña de "datos sensibles" (salud, socioeconómicos) visible/editable **solo si el usuario que mira la pantalla es Dirección** — si es Administrador, se muestra de solo lectura; para el resto de roles esa pestaña ni siquiera debería pedirse al backend
- Crear/editar encargados y su selector para vincular con uno o varios estudiantes (`POST /guardians/{id}/link-student/`), con la lista de vínculos existentes y opción de desvincular
- Asignar docente/tallerista a curso-sección (`POST /assignments/`) — el formulario debe filtrar los cursos disponibles según el tipo de sección elegida (ADR-0001), para no dejar que la persona arme una combinación que el backend va a rechazar

Portal operativo:
- `GET /assignments/?mine=...` (ya scoped por backend a "mis asignaciones") para que un docente/tallerista vea qué tiene asignado — insumo para las pantallas de asistencia y notas de las próximas fases, no hace falta una pantalla dedicada solo para esto todavía.

### Fase 6 — Asistencia (RF-16, RF-12, RF-21)
Portal operativo, rol Docente/Docente con sección a cargo/Tallerista (siempre limitado a sus propias secciones asignadas, el backend ya lo filtra):

- Tomar asistencia diaria de una sección: lista de inscritos con un selector rápido presente/tarde/ausente/justificado por estudiante — HU-16 pide que se pueda hacer durante la clase o al final de la jornada, así que el diseño tiene que permitir guardar parcial y volver
- Si se captura hora de llegada en vez de estado directo, mandar `check_in_time` y dejar que el backend decida presente/tarde (RN-11) — no calcular la tardanza en el frontend
- Pantalla de justificaciones: registrar una (con archivo adjunto opcional) y, para Dirección, resolver (aprobar/rechazar) — la resolución es la única acción restringida a Dirección en toda esta fase
- El documento de respaldo de una justificación se descarga con `GET /justifications/{id}/document/`, nunca con una URL directa (no hay `MEDIA_URL` público a propósito)

Portal administrativo/operativo, para secciones de taller (RF-21):
- Botón "Descargar plantilla" (`GET /attendance/template/{section}/{fecha}/`) y "Subir plantilla" (`POST /attendance/template/upload/`) — la subida devuelve una lista de errores por fila si algo no cuadra (ningún registro se guarda hasta que el archivo esté limpio); el diseño de esta pantalla de errores debe seguir el principio de "vista previa que no es un volcado técnico" de la sección 15.2 del prompt maestro

Portal público (familia), ya con datos reales disponibles para RF-31 (consultar asistencia) — todavía no construido porque esa pantalla específica es Fase 10.

### Fase 7 — Notas (RF-17 a RF-20, RF-23, RF-10)
Portal operativo, rol Docente/Docente con sección a cargo (siempre limitado a sus propias asignaciones, el backend ya lo filtra):

- Diseñar la unidad: agregar actividades una por una viendo en todo momento cuántos puntos van (de 100) y cuántas son pruebas cortas — el backend rechaza pasarse de 100, pero la pantalla debería impedirlo visualmente antes de mandar la petición, no solo mostrar el error
- Capturar punteo real por actividad, uno por uno — si la actividad ya tiene nota, no ofrecer "editar" directo: llevar al formulario de "solicitar corrección" (RF-23), porque el backend ya rechaza el sobrescritura (RN-05)
- Botones "Descargar plantilla" (`GET /grades/template/{assignment}/{unit}/`) y "Subir plantilla", con un paso de vista previa (`POST /grades/template/preview/`) antes de confirmar (`POST /grades/template/upload/`) — la vista previa distingue notas nuevas de modificaciones, así que la pantalla debería mostrar esa distinción, no solo un número total
- Bandeja de solicitudes de modificación propias, con su estado (pendiente/aprobada/rechazada)

Portal administrativo, rol Dirección:
- Bandeja de solicitudes de modificación pendientes de todo el centro, con aprobar/rechazar (`POST /grade-change-requests/{id}/approve|reject/`) — es la única acción de escritura de toda esta fase que no es del docente

Ninguna pantalla debe mostrar `raw_score` en ningún rol — la API ya no lo expone (RN-06), así que no hay manera de mostrarlo aunque alguien lo pidiera; si Dirección necesita ver el historial de una nota, es a través de `original_score`/`requested_score` en la solicitud de modificación, no de un campo "punteo real" suelto.

## Hecho

- **Fase 3** — Login, cambio de contraseña obligatorio, guards de router por rol. (`frontend/src/features/auth/`)
