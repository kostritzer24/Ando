# Fase 10 (frontend) — Portal público: cierre

Séptima fase del bloque de frontend, y la primera que no se limitó a construir sobre backend ya existente: de los 11 RF de la Fase 10 (RF-27 a RF-37), varios no tenían ningún endpoint todavía — a diferencia de las fases anteriores, donde el backend siempre estaba listo desde su propia fase de "solo backend".

## Decisión de alcance (checkpoint con el usuario)

Al revisar el código real (no solo `docs/api.md`, que es un documento de planeación) se encontró que:

- RF-27 (login + selector), RF-29 (notas), RF-31 (asistencia) y RF-33 (solvencia, descarga de documentos) ya tenían backend completo desde las Fases 3, 7, 6 y 9.
- RF-28/RF-32 (calendario semanal y horario del estudiante) y RF-34 (descarga del boletín en PDF) **no tenían ningún endpoint** — son "debe tener" en el plan maestro, así que el usuario aprobó construirlos en esta misma fase (ver el punto de control en la conversación de cierre).
- RF-35 a RF-37 (reportes de conducta, cartelera de avisos, buzón) dependen de `apps/communication`, que no tiene modelos, serializers ni vistas — ese backend está asignado a la Fase 11 ("Comunicación del lado del centro"), que en el plan maestro queda *después* de la Fase 10. El usuario aprobó dejarlos pendientes hasta que se construya la Fase 11.
- RF-30 (puntos que faltan para aprobar) tampoco tenía endpoint y es "debería tener" (no "debe tener") — queda pendiente junto con RF-35 a RF-37.

## Qué se construyó

### Backend (lo mínimo que le faltaba a RF-28/RF-32/RF-34)

- **`GET /calendar/weekly/?student=<id>`** (`scheduling/api/views.py`, `WeeklyCalendarView`): junta el horario recurrente (`ScheduleBlock`) con los eventos de calendario (`CalendarEvent`, institucionales o de una asignación de la sección) del estudiante elegido — exclusivo de Padre de familia, validando el vínculo por `GuardianStudentLink` igual que el resto de endpoints de esta app.
- **`GET /report-cards/{id}/download/`** (`grading/api/views.py`): genera el PDF del boletín al momento de la descarga — el modelo `ReportCard` nunca guardó un archivo aparte a propósito (ver su docstring), así que el contenido (nota por curso, de esa unidad) se calcula ahí mismo con `nota_de_unidad`, sin duplicar el cálculo que ya usa la captura de notas. Plantilla nueva en `apps/grading/templates/grading/boletin.html`, sin QR ni espacio de firma/sello (RN-15 aplica a los documentos emitidos, no al boletín).
- **Bug real corregido:** `nota_de_unidad(enrollment, unit)` nunca se había usado en producción — al ser el primer caso de uso real (el PDF del boletín necesita la nota por curso), se encontró que no filtraba por `assignment`: sumaba las actividades de *todos* los cursos de la unidad, no solo del curso pedido. Se agregó el parámetro `assignment` y una prueba que cubre justo ese caso.
- **Campos denormalizados agregados** (mismo criterio que `TeacherAssignmentSerializer` desde la Fase 5, "para no abrirle el catálogo completo"): `GradeSerializer` gana `course_name`/`unit_number`/`activity_name`/`max_score` (la familia no llega a `/activities/` ni a `/assignments/`, y RF-29 necesita agrupar por curso y unidad); `AttendanceSerializer` gana `section_type` (distinguir jornada matutina de taller sin `/sections/`); `EnrollmentSerializer` gana `section_grade`/`section_letter`/`section_type` (mismo motivo, para el nombre de sección en la cabecera del portal).
- **Bug de datos encontrado y corregido:** `PagosPage.vue`/`DocumentosPage.vue` de la Fase 9 llamaban a `/sections/` para el selector de estudiante — el rol Encargado de pagos no tiene acceso a esa área y la pantalla se rompía entera. Se corrigió quitando esa dependencia (no hacía falta el grado, solo nombre y código).
- **`seed_demo` extendida:** la encargada de demostración ahora tiene **dos** hijos vinculados (María Ximena y Juan Carlos), no uno — la sección 16 del prompt maestro pide explícitamente el flujo de extremo a punta "consultar el portal como encargado con dos hijos" (HU-27).

### Frontend

Todo en una feature nueva, `frontend/src/features/portal/`, con un layout propio (`pages/publico/PublicoLayout.vue`) que usa por primera vez `TopAppBar`, `BottomTabBar` y `DayTabs` — componentes construidos en la Fase 3 siguiendo el mockup de la Propuesta B (`docs/diseno/mockups/propuesta-b-tramite-claro.html`, la pantalla de ejemplo del documento de dirección visual es justo esta) pero nunca conectados hasta ahora.

- **Selector de estudiante (HU-27):** vive en `portalStore.ts` (Pinia), no en cada página, para sobrevivir la navegación entre pestañas. El botón "Cambiar estudiante" de `TopAppBar` abre un modal con la lista de estudiantes vinculados (`GET /students/`, que ya llega filtrado al encargado autenticado — no hizo falta el endpoint `/me/students/` que `docs/api.md` había planeado, el `/students/` general ya resuelve HU-27 con su alcance por rol).
- **`InicioPage.vue`** (RF-28/RF-32): pestañas de lunes a viernes de la semana real en curso (`DayTabs`), agenda del día elegido mezclando bloques de horario (con la hora de `PERIODOS`, ya definida desde la Fase 8) y eventos de calendario de esa fecha, con `TagPill` para distinguir taller de aviso institucional.
- **`NotasPage.vue`** (RF-29/RF-34): notas agrupadas por curso y por unidad a partir de los campos denormalizados de `Grade`, con la lista de actividades de cada unidad; debajo, la bandeja de boletines publicados con "Descargar" (PDF real).
- **`AsistenciaPage.vue`** (RF-31): agrupada en "Jornada matutina" y "Taller" con `section_type`, estado con `TagPill` (presente/tarde en verde-aviso, ausente en alerta).
- **`PagosPage.vue`** (RF-33): mismo patrón visual que el de Dirección/Pagos de la Fase 9 pero de solo lectura — estado de solvencia y bandeja de constancias de solvencia ya emitidas, con "Descargar".
- **`VerificarPage.vue`** (RF-14, corrección de un pendiente de la Fase 9): página pública sin sesión en `/verificar/:codigo`, fuera de cualquier layout — se había construido el backend en la Fase 9 pero no la pantalla.

## Verificación real

`vue-tsc --noEmit`, `eslint` y `vitest run` (34 pruebas) sin errores. Backend: 298 pruebas (10 nuevas), 100 % de cobertura en los servicios tocados.

1 prueba de extremo a punta contra un navegador real (Chromium), con el backend vivo y datos de `seed_demo`: se arma horario, aviso institucional, una nota y asistencia por API directa (como Dirección, sin repetir los flujos de horario/notas/asistencia que ya prueban sus propias fases), se publica un boletín, y como familia.demo se recorren las cuatro pestañas del portal — calendario con la clase y el aviso, notas con la nota real y descarga del boletín, asistencia agrupada, solvencia con descarga de constancia — más el cambio de estudiante (María, apellido "Pérez Tzul", no es la elegida por omisión: "López Xitumul" ordena antes por apellido, así que Juan Carlos sale primero — hubo que elegir a María explícitamente en la prueba) y, para cerrar, la verificación pública por código QR de la constancia recién emitida, con y sin código válido.

## Siguiente

Fase 11 (comunicación del lado del centro): backend nuevo de `apps/communication` (avisos, reportes de conducta, buzón con filtro de palabras inapropiadas y bloqueo temporal — RF-13, RF-24, RF-25, RNF-10, RN-16) más su frontend administrativo/operativo. Después de esa Fase 11, quedan pendientes de este documento RF-30 (puntos para aprobar) y RF-35 a RF-37 en el portal público.
