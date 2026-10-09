# Hallazgos — Set B — Gabriela

Fecha: 2026-10-07 · Rama/commit probado: `fase-15-formatos-institucionales @ 1f92784` · Navegador: Chrome (DevTools) · SO: Windows 11

Copia el bloque de abajo una vez por hallazgo. IDs consecutivos: `B-001`, `B-002`…
Una cosa por hallazgo (si son dos problemas, son dos hallazgos). Si algo **pasó bien**, no hace falta anotarlo; solo marca el caso en la tabla de cobertura al final.

> **Nota de la sesión asistida por API.** Los hallazgos B-001 a B-006 salieron de probar en el navegador. B-007 a B-009 y las ✅ de los permisos (JUS-02, HOR-02, HOR-05, ASG-01, ASG-02, EST-02, EST-05, ASG-04, ASI-04/07/08, JUS-01) se verificaron con `curl`/`Invoke-RestMethod` contra `http://localhost:8000/api/v1` autenticándose como cada rol — el prompt-tester lo contempla ("puedes usar `curl` contra la API con mi token"). Los casos de UI (TRV, PDFs, móvil 375 px, teclado, consola) **siguen pendientes de verificación en pantalla por la tester**; no se pueden cerrar por API.

---

### B-001 · Cualquier rol con "ver" en Asistencia puede descargar la nómina de un taller que no tiene a cargo

- **Caso del plan:** PLA-04 (y toca PER-05 del Set A)
- **Tipo:** seguridad / permisos
- **Severidad:** Crítica
- **Rol con el que ocurrió:** `docente.demo` (rol "Docente", sin ninguna asignación de taller)
- **Dónde:** `GET http://localhost:8000/api/v1/attendance/template/{section_public_id}/{fecha}/` — endpoint directo, no hay pantalla para este rol en el frontend (lo bloquea), pero el backend sí responde.
- **Referencia:** RF-21 (plantilla de asistencia de talleres: solo DIR/Tallerista según `docs/permisos-roles.md`), RNF-04 / sección 14.2 del `PROMPT_MAESTRO` (nombres y códigos internos son datos personales — no deben llegar a un rol sin alcance sobre esa sección).
- **Pasos para reproducir:**
  1. Levantar backend y frontend. Login en Chrome como `dir.demo`.
  2. En DevTools → Network → Fetch/XHR, entrar a Catálogo → Secciones y copiar el `public_id` de una sección de tipo `taller` (en la base `seed_demo` es `Taller de panadería`, `public_id = 81ead3b6-4c4b-43c1-b2ec-5a81f632a87e`).
  3. En una terminal nueva, loguearse por API como `docente.demo` y guardar el token de acceso:
     ```powershell
     $body  = @{ username='docente.demo'; password='CambiaEstaClave2026' } | ConvertTo-Json
     $login = Invoke-RestMethod -Uri 'http://localhost:8000/api/v1/auth/login/' -Method Post -Body $body -ContentType 'application/json'
     $token = $login.access
     ```
     `$login.user.role_name` devuelve `"Docente"` — confirma que no es tallerista ni Dirección.
  4. Pedir la plantilla de la sección del punto 2 con ese token:
     ```powershell
     Invoke-WebRequest `
       -Uri 'http://localhost:8000/api/v1/attendance/template/81ead3b6-4c4b-43c1-b2ec-5a81f632a87e/2026-10-06/' `
       -Headers @{ Authorization = "Bearer $token" } `
       -OutFile "$env:USERPROFILE\Downloads\fuga-plantilla.xlsx" -PassThru
     ```
  5. Abrir el `.xlsx` resultante.
- **Esperado:** `403 Forbidden`. Un Docente académico, sin ninguna asignación en ese taller, no debe obtener su nómina — ni la pantalla ni la API. Según la matriz, solo Dirección y Tallerista llegan a la plantilla, y Tallerista limitado a sus propias secciones (igual que la pantalla de "subir plantilla" ya valida en `AttendanceTemplateUploadView`).
- **Obtenido:** `200 OK`, `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`, archivo descargado con la nómina real del taller: fila de encabezados "Código / Nombre / Estado…" y filas con el código interno y nombre completo de cada estudiante inscrito (p. ej. `ES001 — María Ximena Pérez Tzul`).
- **Reproducible:** siempre.
- **Evidencia:**
  - Salida de `Invoke-WebRequest`:
    ```
    Status: 200
    Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
    Archivo: C:\Users\Gabriela Lopez\Downloads\fuga-plantilla.xlsx
    ```
  - Archivo `fuga-plantilla.xlsx` en `Downloads` con el roster del taller (fila 1 encabezados; fila 2 en adelante `ES###` + nombre completo).
- **Viewport:** no aplica (API directa; también afectaría a cualquier UI que llame al endpoint).
- **Hipótesis de causa (hipótesis):** `backend/apps/attendance/api/views.py:162-182` (`AttendanceTemplateDownloadView.get`) solo exige `area="asistencia"` (nivel `ver`) y no verifica que la sección pertenezca a una asignación activa del usuario. La vista hermana de subida (`AttendanceTemplateUploadView`, línea 223) sí llama a `_seccion_asignada_al_docente(request.user, section)` antes de procesar — la descarga quedó sin esa misma validación. Además, con la matriz actual todo rol con `ver` sobre `asistencia` (Docente, Guía, Dirección, Coordinación, Admin, incluso Pagos si tuviera `ver`) atraviesa el permiso, no solo el Tallerista.

---

### B-002 · "Inscribir estudiante" acepta fechas de nacimiento futuras y absurdamente antiguas

- **Caso del plan:** EST-03
- **Tipo:** falta-funcionalidad / datos
- **Severidad:** Alta (datos basura en el registro de estudiantes; no se puede confiar en la edad calculada ni en reportes derivados; el estudiante queda inscrito y "activo" sin posibilidad de que el formulario lo señale)
- **Rol con el que ocurrió:** `dir.demo` (rol "Dirección")
- **Dónde:** pantalla `/administrativo/estudiantes` → botón "Inscribir estudiante". API: `POST /api/v1/students/`.
- **Referencia:** no documentado como RF/RN; el plan lo espera en EST-03 ("fechas de nacimiento imposibles/futuras | Validación"). Entra como ux/falta-funcionalidad.
- **Pasos para reproducir:**
  1. Login como `dir.demo`.
  2. Menú → **Estudiantes** → **Inscribir estudiante**.
  3. Nombres: `Prueba`, Apellidos: `FechaFutura`, **Fecha de nacimiento: `2099-01-01`**, Sección: la primera disponible, Beca: Ninguna. Clic **Inscribir**.
  4. Repetir el formulario con Apellidos: `FechaAntigua` y **Fecha de nacimiento: `1800-01-01`**.
- **Esperado:**
  - En ambos intentos, el formulario rechaza antes de enviar (o el backend responde `400`) con un mensaje junto al campo "Fecha de nacimiento" en español sencillo, p. ej. "La fecha de nacimiento no puede ser futura" / "Revisá la fecha de nacimiento". El estudiante no se crea.
  - El `<input type="date">` del formulario (`EstudiantesPage.vue:163`) no limita el rango con `min`/`max`, y el `StudentCreateSerializer` (`backend/apps/students/api/serializers.py:29-34`) solo tiene `birth_date = serializers.DateField()` sin validador — así que ninguna de las dos capas intercepta la fecha.
- **Obtenido:** ambos ingresos se crean con `201 Created`. El segundo caso además asigna código `ES006`, lo que ocupa un consecutivo real del centro con un registro de prueba.
  - Prueba 1 (futura):
    ```json
    {
      "public_id": "efe7a9b0-2162-4636-a503-7db369889507",
      "internal_code": "ES005",
      "first_name": "Prueba",
      "last_name": "FechaFutura",
      "birth_date": "2099-01-01",
      "is_active": true
    }
    ```
  - Prueba 2 (antigua):
    ```json
    {
      "public_id": "b8de8cf3-120a-4208-9b16-e2748f93a405",
      "internal_code": "ES006",
      "first_name": "Prueba",
      "last_name": "FechaAntigua",
      "birth_date": "1800-01-01",
      "is_active": true
    }
    ```
- **Reproducible:** siempre.
- **Evidencia:** respuestas JSON de arriba (del cuerpo de `POST /api/v1/students/`, status 201 en ambos). Los dos registros quedan visibles en la lista de estudiantes de `dir.demo` con la fecha absurda a la vista.
- **Viewport:** escritorio (también falla en móvil 375 px, es el mismo endpoint).
- **Hipótesis de causa (hipótesis):** falta validación en ambas capas.
  - Frontend: `frontend/src/features/estudiantes/components/EstudiantesPage.vue:163` usa `FormField … tipo="date"` sin `max` (debería ser `max="hoy"` y un `min` razonable, p. ej. 1950 o la mayoría de edad legal del centro).
  - Backend: `backend/apps/students/api/serializers.py:29-34` — `birth_date = serializers.DateField()` sin validadores. El validador tendría que vivir acá y/o en `apps/students/services/student.py:crear_estudiante` para que no dependa del cliente.

---

### B-003 · "Publicar evento" en el calendario acepta fecha pasada y hora de fin anterior a la de inicio

- **Caso del plan:** CAL-02
- **Tipo:** falta-funcionalidad / datos
- **Severidad:** Media (no corrompe datos, pero deja eventos imposibles en el calendario institucional que ven docentes y familias — RF-28/RF-32 — y en el peor caso un evento con `end_time < start_time` se muestra "al revés" o con duración negativa en vistas que calculen la ventana)
- **Rol con el que ocurrió:** `dir.demo` (rol "Dirección")
- **Dónde:** `/administrativo/calendario` → botón "Publicar evento". API: `POST /api/v1/calendar-events/`.
- **Referencia:** no documentado como RF/RN; el plan lo espera en CAL-02 ("fecha pasada, rango invertido, solapados, todo el día | Validación"). Entra como ux/falta-funcionalidad.
- **Pasos para reproducir:**
  1. Login como `dir.demo`. Menú → **Calendario**.
  2. **Variante A — fecha pasada:** "Publicar evento" → Título `Prueba Fecha Pasada`, Tipo `Institucional`, **Fecha `01/01/2020`**, Hora inicio `08:00`, Hora fin `09:00`, sin asignación. Guardar.
  3. **Variante B — rango invertido:** "Publicar evento" → Título `Prueba Rango Invertido`, Tipo `Institucional`, **Fecha `15/11/2026`**, **Hora inicio `10:00`**, **Hora fin `09:00`**, sin asignación. Guardar.
- **Esperado:** en ambas variantes el formulario rechaza antes de enviar (o la API responde `400`) con un mensaje junto al campo:
  - Variante A: "La fecha no puede ser anterior a hoy" (o similar).
  - Variante B: "La hora de fin tiene que ser posterior a la de inicio".
  El evento no se crea en ninguno de los dos casos.
- **Obtenido:** las dos variantes se crearon con éxito; el modal cerró y los dos eventos quedaron visibles en la tabla del calendario. Respuestas del `POST /api/v1/calendar-events/`:
  - Variante A:
    ```json
    {
      "public_id": "00219dd0-4d10-43c2-beca-e654e596fb21",
      "title": "Prueba Fecha Pasada",
      "type": "institucional",
      "event_date": "2020-01-01",
      "start_time": "08:00:00",
      "end_time": "09:00:00",
      "published_by": "dir.demo",
      "is_active": true
    }
    ```
  - Variante B:
    ```json
    {
      "public_id": "e0f9bf95-5453-416d-a0ac-19679fd693d2",
      "title": "Prueba Rango Invertido",
      "type": "institucional",
      "event_date": "2026-11-15",
      "start_time": "10:00:00",
      "end_time": "09:00:00",
      "published_by": "dir.demo",
      "is_active": true
    }
    ```
- **Reproducible:** siempre.
- **Evidencia:** respuestas JSON de arriba. Los dos eventos quedan listados en `/administrativo/calendario` para `dir.demo` y, por `WeeklyCalendarView`, también pueden alcanzar al portal familiar según la sección.
- **Viewport:** escritorio (el formulario es el mismo en móvil 375 px).
- **Hipótesis de causa (hipótesis):** falta validación en las tres capas que podrían hacerla.
  - Frontend: `frontend/src/features/horarios/components/CalendarioPage.vue:206-222` — los `<input type="date">` y `<input type="time">` no llevan `min`/`max` ni validación JS que compare `end_time` contra `start_time` antes de llamar a `calendarEventsApi.crear`.
  - Backend serializer: `backend/apps/scheduling/api/serializers.py:53-80` (`CalendarEventSerializer`) solo expone los campos — no tiene `validate_event_date` ni un `validate` que compare las horas.
  - Backend servicio/dominio: `backend/apps/scheduling/services/calendar_event.py:9-39` (`crear_evento`) solo valida tipo y autor con `validar_creacion` (`backend/apps/scheduling/domain/calendar_event.py`), que a su vez tampoco revisa fecha ni rango horario.
- **Para la limpieza:** los dos eventos quedan en la base; mientras no se arreglen, se pueden quitar desde la misma pantalla con el botón "Eliminar" de cada fila (hace baja lógica, no afecta nada más).

---

### B-004 · "Tomar asistencia" acepta sábado, domingo y fecha claramente futura sin validación ni advertencia

- **Caso del plan:** ASI-05
- **Tipo:** falta-funcionalidad / datos
- **Severidad:** Media (ensucia los reportes de asistencia con fechas imposibles: fines de semana en que el centro no abre y fechas futuras — un click accidental deja al estudiante "presente" el 1 de enero de 2099, dato que después se mezcla en RF-15 y en el portal de familia; no corrompe los datos reales pero compite con ellos)
- **Rol con el que ocurrió:** `guia.demo` (rol "Docente con sección a cargo")
- **Dónde:** `/operativo/tomar-asistencia` (portal operativo). API: `POST /api/v1/attendance/`.
- **Referencia:** no documentado como RN/HU — el plan lo espera en ASI-05 ("Fecha futura, fin de semana, día sin clases, fecha muy pasada | Validación o advertencia razonable"). Entra como ux/falta-funcionalidad.
- **Pasos para reproducir:**
  1. Login como `guia.demo` → **Tomar asistencia**.
  2. Elegir una sección cualquiera. En el campo **Fecha**, escribir `10/10/2026` (sábado). Clic en **"Presente"** de un estudiante.
  3. Repetir con **Fecha `01/01/2099`** (futura muy lejana). Clic **"Presente"**.
  4. Repetir con **Fecha `11/10/2026`** (domingo). Clic **"Presente"**.
- **Esperado:** la pantalla rechaza con mensaje junto al campo Fecha, o al menos avisa "Esta fecha no corresponde a un día de clases" / "Esta fecha es futura" antes de guardar. No se crea asistencia.
- **Obtenido:** las tres variantes se guardan con `201 Created`. Los `POST /api/v1/attendance/` devuelven:
  - Sábado:
    ```json
    {
      "public_id": "d9f10073-e233-42a9-b088-4943b8c5d155",
      "enrollment": "c18bef8f-78b6-4e3b-8f89-c94d85586980",
      "date": "2026-10-10",
      "status": "presente",
      "source": "manual",
      "recorded_by": "guia.demo",
      "section_type": "academica",
      "is_active": true
    }
    ```
  - Futura:
    ```json
    {
      "public_id": "9f2b9944-f887-47db-8278-43f861b243b9",
      "enrollment": "c18bef8f-78b6-4e3b-8f89-c94d85586980",
      "date": "2099-01-01",
      "status": "presente",
      "source": "manual",
      "recorded_by": "guia.demo",
      "section_type": "academica",
      "is_active": true
    }
    ```
  - Domingo:
    ```json
    {
      "public_id": "53b403cc-c404-4599-a5d6-cc2928d8201a",
      "enrollment": "c18bef8f-78b6-4e3b-8f89-c94d85586980",
      "date": "2026-10-11",
      "status": "presente",
      "source": "manual",
      "recorded_by": "guia.demo",
      "section_type": "academica",
      "is_active": true
    }
    ```
- **Reproducible:** siempre.
- **Evidencia:** las tres respuestas JSON de arriba. Pueden verse en el portal de familia del estudiante (RF-31) una vez que el padre vinculado abra "Asistencia".
- **Viewport:** escritorio (comportamiento idéntico en móvil 375 px, es el mismo endpoint y el mismo `<input type="date">`).
- **Hipótesis de causa (hipótesis):** falta validación en ambas capas.
  - Frontend: `frontend/src/features/asistencia/components/TomarAsistenciaPage.vue:196` usa `<input type="date">` sin `min`/`max` y sin lógica JS que verifique día de la semana o rango razonable.
  - Backend serializer: `backend/apps/attendance/api/serializers.py:35-46` (`AttendanceCreateSerializer`) solo tiene `date = serializers.DateField()`; el servicio `apps/attendance/services/attendance.py:registrar_asistencia` tampoco verifica el día.
  - El centro trabaja de lunes a viernes (RN-13 implica semana escolar de L-V). Una validación mínima sería `fecha.weekday() < 5` y `fecha <= hoy + 1 día`.
- **Para la limpieza:** los tres registros se pueden desactivar desde Bitácora/Asistencia editando, o quedar como están — no interfieren con el resto de pruebas mientras sean del mismo estudiante en días no reales.

---

### B-006 · Se pueden registrar varias justificaciones activas sobre la misma falta

- **Caso del plan:** JUS-04
- **Tipo:** falta-funcionalidad / datos
- **Severidad:** Media (dejar dos pendientes abre la puerta a historial incoherente: si Dirección aprueba la primera y rechaza la segunda, la asistencia queda `justificado` pero una de las justificaciones aparece "rechazada" sobre un hecho ya resuelto; y al revés, dos aprobaciones ejecutan `asistencia.status = ESTADO_JUSTIFICADO` dos veces y dejan la bitácora confusa — RN-05 habla de conservar historial, no de duplicarlo)
- **Rol con el que ocurrió:** `guia.demo` (rol "Docente con sección a cargo")
- **Dónde:** `/operativo/justificaciones`. API: `POST /api/v1/justifications/`.
- **Referencia:** no documentado como RN/HU — el plan lo espera en JUS-04 ("duplicar | Validación").
- **Pasos para reproducir:**
  1. Login como `guia.demo` → **Tomar asistencia** → crear una falta: elegir una sección, fecha de hoy, marcar un estudiante como **Ausente**. Guardar el `attendance.public_id` de la respuesta.
  2. Menú → **Justificaciones** → "Registrar justificación".
  3. Falta a justificar: la ausencia del paso 1. Tipo: "Motivo familiar". Motivo: `Prueba 1`. Guardar.
  4. "Registrar justificación" otra vez. **Misma falta** (sigue apareciendo en el dropdown). Tipo: "Motivo familiar". Motivo: `Prueba 2`. Guardar.
- **Esperado:** el segundo "Guardar" rechaza con mensaje tipo "Esta falta ya tiene una justificación pendiente". O al menos la UI quita del dropdown las faltas que ya tienen una justificación activa (pendiente o aprobada).
- **Obtenido:** las dos justificaciones se crean exitosamente (`201 Created`). Al listar `GET /api/v1/justifications/` quedan dos filas apuntando a la misma `attendance`:
  ```json
  {
    "count": 2,
    "results": [
      {
        "public_id": "c5287433-bedc-4c60-bf8e-218f95ed8efe",
        "attendance": "d575e5a3-9969-4ce3-aefc-51c5470cb612",
        "justification_type": "ac0ac8bc-2844-4444-be08-f64ba9e8e920",
        "reason_detail": "Prueba 2 — segundo intento sobre la misma falta",
        "resolution": "pendiente",
        "submitted_by": "guia.demo"
      },
      {
        "public_id": "63b7c5c3-f313-4b71-85ee-4d84c5d96f6a",
        "attendance": "d575e5a3-9969-4ce3-aefc-51c5470cb612",
        "justification_type": "ac0ac8bc-2844-4444-be08-f64ba9e8e920",
        "reason_detail": "Prueba 1 — primer intento",
        "resolution": "pendiente",
        "submitted_by": "guia.demo"
      }
    ]
  }
  ```
- **Reproducible:** siempre.
- **Evidencia:** respuesta JSON arriba. Las dos filas quedan visibles en la tabla de Justificaciones para `guia.demo` y para Dirección, cada una con sus propios botones "Aprobar/Rechazar" (que podrían resolverse en sentidos opuestos).
- **Viewport:** escritorio (mismo endpoint en móvil).
- **Hipótesis de causa (hipótesis):** no hay restricción en ninguna capa.
  - Modelo: `backend/apps/attendance/models.py:54-109` (`Justification`) no tiene `UniqueConstraint` por `attendance` ni por `(attendance, resolution="pendiente")`.
  - Servicio: `backend/apps/attendance/services/justification.py:6-21` (`crear_justificacion`) no verifica si ya hay una pendiente o aprobada para esa `attendance`.
  - Frontend: `frontend/src/features/asistencia/components/JustificacionesPage.vue:50-54` arma `opcionesAsistencia` filtrando solo por `status` de la asistencia; no excluye las que ya tienen justificación activa.
- **Pregunta de diseño adicional (hipótesis):** incluso si se mantuviera "una justificación por falta", vale aclarar en el prompt maestro qué pasa si una se rechaza — ¿se puede abrir otra, o la falta queda sin posibilidad de nueva justificación? Hoy el código permite N justificaciones y el documento no define el límite.

---

### B-007 · POST /attendance/ con `(enrollment, date)` ya existente devuelve 500 (IntegrityError crudo) en vez de 400

- **Caso del plan:** ASI-09 (doble envío / doble escritura)
- **Tipo:** bug / seguridad
- **Severidad:** Alta (cualquier doble-clic del docente en "Presente", o un reintento tras timeout, revienta con 500 y el frontend muestra el banner genérico "No se pudo guardar la asistencia de ese estudiante"; además en entornos con `DEBUG=True` filtra el stack trace y el SQL — RNF-07 pide bitácora pulcra, no páginas de error de Django)
- **Rol con el que ocurrió:** `dir.demo` (reproducible con cualquiera que tenga `editar` en asistencia).
- **Dónde:** `POST /api/v1/attendance/`.
- **Referencia:** `Attendance.Meta.constraints` tiene `UniqueConstraint(fields=["enrollment", "date"], name="asistencia_unica_por_dia")` (`backend/apps/attendance/models.py:46-48`), así que es una regla declarada. El plan la cubre en ASI-09 ("Doble envío / dos usuarios tomando la misma asistencia a la vez | No duplica; última escritura clara").
- **Pasos para reproducir (vía API, equivalente a doble-clic en la UI):**
  1. Registrar una asistencia para una inscripción y fecha, p. ej.:
     ```powershell
     Invoke-RestMethod -Uri 'http://localhost:8000/api/v1/attendance/' -Method Post `
       -Headers @{Authorization = "Bearer <token-dir>"} -ContentType 'application/json' `
       -Body '{"enrollment":"e68d0fbf-7fca-4bd4-ab6b-46f799f2fa65","date":"2026-10-06","status":"ausente"}'
     ```
     Devuelve `201 Created`.
  2. Reenviar exactamente el mismo cuerpo (o uno con otro `status`): `curl -X POST ... -d '{"enrollment":"e68d0fbf-...","date":"2026-10-06","status":"presente"}'`.
- **Esperado:** `400 Bad Request` con cuerpo tipo `{"non_field_errors":["Ya hay una asistencia registrada para este estudiante en esa fecha."]}` — la UI puede ofrecer "¿querés actualizarla con el nuevo estado?" en vez de duplicar.
- **Obtenido:** `500 Internal Server Error`. El cuerpo es la página de debug de Django con `IntegrityError at /api/v1/attendance/` (confirmado con `curl -o … -w "%{http_code}"`); con `DEBUG=False` quedaría un 500 genérico.
- **Reproducible:** siempre.
- **Evidencia:** salida de dos POST consecutivos con el mismo payload — el primero devuelve 201, el segundo retorna status HTTP 500 y la respuesta empieza con `<!DOCTYPE html>…<title>IntegrityError at /api/v1/attendance/</title>`.
- **Viewport:** no aplica (API). En la UI se traduce al banner genérico "No se pudo guardar la asistencia de ese estudiante — Reintentar".
- **Hipótesis de causa (hipótesis):**
  - `backend/apps/attendance/services/attendance.py:13-35` (`registrar_asistencia`) hace `Attendance.objects.create(...)` sin capturar `IntegrityError`.
  - `backend/apps/attendance/api/views.py:74-95` (`AttendanceViewSet.create`) solo atrapa `FaltaEstadoOHoraDeLlegada`, no el `IntegrityError` que lanza la restricción única.
  - Alternativa: en el servicio hacer `Attendance.objects.update_or_create(...)` si se quiere que la segunda escritura actualice el estado (comportamiento esperado en ASI-04 "editar una asistencia ya guardada").

---

### B-008 · Una justificación ya resuelta se puede re-resolver sin control (aprobada ↔ rechazada), y la asistencia no vuelve atrás

- **Caso del plan:** JUS-03 / MOD-06 (relacionado) — "resolver una ya resuelta | Manejo coherente"
- **Tipo:** falta-funcionalidad / datos
- **Severidad:** Media (afecta trazabilidad y abre un camino raro: Dirección aprueba, se arrepiente y "rechaza" la misma justificación — la asistencia queda `justificado` para siempre aunque la resolución diga `rechazada`; `resolved_by` y `resolved_at` se sobrescriben, perdiendo quién tomó qué decisión y cuándo)
- **Rol con el que ocurrió:** `dir.demo`
- **Dónde:** `POST /api/v1/justifications/{public_id}/resolve/`.
- **Referencia:** RF-12 ("resolución la decide Dirección, caso por caso"), RN-12. El plan contempla el "resolver una ya resuelta" en MOD-06 para Set C; vale igual acá porque la rompe en el flujo de justificaciones.
- **Pasos para reproducir:**
  1. Crear una justificación sobre una falta `ausente` (B-006).
  2. `dir.demo` POST `/justifications/{pid}/resolve/` con `{"aprobar": true}` → asistencia pasa a `justificado`. OK.
  3. `dir.demo` POST el **mismo** `/justifications/{pid}/resolve/` con `{"aprobar": false}` → la justificación cambia a `rechazada`, pero…
  4. GET `/attendance/{aid}/` → sigue en `justificado`.
- **Esperado:** una vez resuelta, un segundo `/resolve/` sobre la misma justificación debe:
  - rechazarse con `400`/`409` ("Esta justificación ya está resuelta"), o
  - documentar explícitamente que la decisión se puede cambiar y, en ese caso, (a) revertir el estado de la asistencia según corresponda (si rechaza una antes aprobada, volver la falta a `ausente`, salvo que otra justificación aprobada la cubra) y (b) guardar historial (no sobrescribir `resolved_by`/`resolved_at`).
- **Obtenido:** las dos llamadas devuelven `200 OK` y el estado del sistema queda incoherente:
  ```
  Justificación c5287433 — resolution=aprobada → re-resolve rechazada → resolution=rechazada
  Asistencia d575e5a3 — ausente → justificado → (sigue) justificado
  resolved_by/resolved_at — se pisaron en cada llamada
  ```
- **Reproducible:** siempre.
- **Evidencia:** salida de la secuencia de llamadas (`$ curl -X POST .../resolve/` dos veces sobre la misma justificación con payloads `{aprobar:true}` y luego `{aprobar:false}` — status 200 en ambos).
- **Viewport:** no aplica (API; UI expone el mismo botón si Dirección vuelve a abrir la justificación).
- **Hipótesis de causa (hipótesis):** `backend/apps/attendance/services/justification.py:24-41` (`resolver_justificacion`) escribe `resolution`/`resolved_by`/`resolved_at` directamente y, si la nueva resolución es "aprobada", marca la asistencia como `ESTADO_JUSTIFICADO`. No chequea si ya hay una resolución previa, y no revierte la asistencia cuando se pasa a "rechazada". Faltaría:
  - un `if justificacion.resolution != RESOLUCION_PENDIENTE: raise …` para hacer la resolución inmutable (opción conservadora), o
  - un flujo explícito de "revocar aprobación" que revierta la asistencia a su estado anterior y guarde historial en bitácora.

---

### B-009 · Un docente no ve eventos de calendario publicados por otro docente de la misma sección

- **Caso del plan:** CAL-01 (periferia) — "docente crea/edita solo los suyos (RN-17)"
- **Tipo:** falta-funcionalidad / ux
- **Severidad:** Media (coordinación entre docentes de la misma sección queda rota: si docente A publica "Entrega del libro del martes" en 1°A, la maestra guía de esa misma sección — docente B — no se entera por el calendario; sí lo ven las familias de esa sección, pero no sus compañeros docentes). El prompt maestro no obliga explícitamente a que un docente vea los eventos de otros en su misma sección, pero en la práctica es el único lugar lógico donde coordinarse.
- **Rol con el que ocurrió:** `guia.demo` (rol "Docente con sección a cargo"), que comparte sección 1°A con `docente.demo` (rol "Docente").
- **Dónde:** `GET /api/v1/calendar-events/`. Y por tabla en pantalla: `/operativo/calendario`.
- **Referencia:** no documentado explícitamente — RN-17 solo habla de edición ("cada docente edita solo las asignaciones que publicó"); la lectura queda abierta. Entra como ux/falta-funcionalidad.
- **Pasos para reproducir:**
  1. Login como `dir.demo` → **Asignaciones** → crear una asignación para `docente.demo` en la misma sección donde `guia.demo` ya tiene asignaciones (p. ej. 1°A, curso Ciencias sociales).
  2. Login como `docente.demo` → **Calendario** → "Publicar evento": Tipo `Asignación docente`, Asignación = la nueva (su asignación en 1°A), fecha futura, materiales. Guardar.
  3. Login como `guia.demo` → **Calendario** → listado.
- **Esperado:** `guia.demo` ve el evento publicado por `docente.demo` porque también enseña en 1°A (y porque las familias de 1°A lo ven vía `WeeklyCalendarView`). Puede no editarlo (eso lo cubre RN-17), pero verlo le sirve para coordinar.
- **Obtenido:** `guia.demo` ve solo los eventos institucionales y los que ella misma publicó (`count=2`, ambos institucionales). El evento publicado por `docente.demo` (confirmed via `dir.demo`) no aparece.
- **Reproducible:** siempre.
- **Evidencia:** salida de `GET /calendar-events/` como `guia.demo` (count=2, ambos tipo=institucional) vs. existencia del evento `82ca61b1-b6df-40ae-b879-5aff2cf0cafd` publicado por `docente.demo` sobre la asignación `7309b6b0-...` de 1°A.
- **Viewport:** escritorio.
- **Hipótesis de causa (hipótesis):** `backend/apps/scheduling/api/views.py:92-107` (`CalendarEventViewSet.scope_queryset`) para `_ROLES_DOCENTES` filtra con `Q(published_by=user) | Q(type=CalendarEvent.TIPO_INSTITUCIONAL)`. No incluye eventos cuya `assignment__section` coincida con alguna sección donde el usuario tiene una asignación activa. Agregar esa tercera cláusula (`| Q(assignment__section__in=secciones_del_usuario)`) alinearía la visibilidad del docente con la que la familia ya tiene vía `WeeklyCalendarView`.
- **Pregunta de diseño:** confirmar con el centro si docentes deben ver eventos de otros docentes de su sección (recomendable) o si la coordinación va por otro canal — RN-17 solo norma la edición.

---

### B-010 · El formulario "Inscribir estudiante" ignora los errores por campo que devuelve el backend

- **Caso del plan:** TRV-03 (formularios)
- **Tipo:** ux / falta-funcionalidad
- **Severidad:** Alta (bloqueo invisible: la Dirección clickea "Inscribir" con un campo vacío y nada pasa — ni mensaje, ni cambio en pantalla, ni indicación del campo faltante; el modal queda abierto como si nada; la única manera de saber qué pasó es abriendo DevTools, lo cual no es un flujo esperado para la usuaria del centro)
- **Rol con el que ocurrió:** `dir.demo` (reproducible con cualquiera que inscriba estudiantes).
- **Dónde:** `/administrativo/estudiantes` → botón "Inscribir estudiante". API: `POST /api/v1/students/`.
- **Referencia:** TRV-03 del plan ("Formularios: campos obligatorios, mensajes de error **junto al campo** y en español sencillo, **no se pierden los datos escritos tras un error**, no se envía vacío"). RNF-08 (texto claro).
- **Pasos para reproducir:**
  1. Login como `dir.demo` → **Estudiantes** → "Inscribir estudiante".
  2. Dejar los campos vacíos y clickear "Inscribir". (También se dispara con cualquier campo faltante — p. ej. tipear solo "Elena" en Nombres y clickear.)
  3. Observar la pantalla: el modal sigue abierto, el botón vuelve a estar activo, no aparece ningún mensaje.
  4. Abrir DevTools → Network → fila `POST /api/v1/students/`.
- **Esperado:** el modal muestra el mensaje por campo (o al menos arriba del formulario) con los errores que el backend ya devuelve, p. ej. "Este campo no puede estar en blanco" bajo cada campo faltante. Los datos escritos se mantienen (confirmado: Elena sigue en el campo — eso sí funciona).
- **Obtenido:** el backend responde `400 Bad Request` con cuerpo bien armado en español:
  ```json
  {
    "first_name": ["Este campo no puede estar en blanco."],
    "last_name": ["Este campo no puede estar en blanco."],
    "birth_date": ["Fecha con formato erróneo. Use uno de los siguientes formatos en su lugar: YYYY-MM-DD."]
  }
  ```
  Pero el frontend **no renderiza nada** de ese cuerpo. La única señal visible al usuario es "no pasó nada tras clickear Inscribir".
- **Reproducible:** siempre.
- **Evidencia:** cuerpo del 400 arriba. Pantalla sin mensaje (verificado por la tester). Datos escritos sí se preservan en el modal.
- **Viewport:** escritorio (también en móvil 375 px, es el mismo modal).
- **Hipótesis de causa (hipótesis):** `frontend/src/features/estudiantes/components/EstudiantesPage.vue:86-116` (`inscribir`) hace `catch { error.value = "No se pudo inscribir al estudiante. Revisá los datos e intentá de nuevo." }`. Pero (a) tira el cuerpo del error del backend (`err.response.data`) sin mapearlo a los campos, y (b) `error.value` se renderiza en `<ErrorBanner v-if="error" ... />` que está en la página detrás del `<AppModal>` — mientras el modal está abierto, el banner no se ve. Faltaría:
  - Capturar `err.response.data` del Axios error, mapearlo a `erroresPorCampo` reactivos, y mostrarlo bajo cada `<FormField>` (que ya acepta prop de error en otros formularios del proyecto).
  - O al menos mover un `<p class="estudiantes-page__error">` arriba del `<form>` dentro del modal con `error`.
- **Mismo patrón en otras pantallas (hipótesis, no verificado):** los formularios de "Nueva asignación" (`AsignacionesPage.vue`), "Publicar evento" (`CalendarioPage.vue`), "Registrar justificación" (`JustificacionesPage.vue`) siguen el mismo molde (`error.value = "..."` dentro del catch y `<ErrorBanner v-if="error">` detrás del modal). Vale la pena mirarlos y, si el patrón se repite, levantar hallazgos vinculados a este.

---

### B-011 · Las fechas en listados salen en formato ISO (`2015-01-01`) en vez de formato humano (`01/01/2015`)

- **Caso del plan:** TRV-08 (fechas y números: "formato consistente **dd/mm/aaaa**")
- **Tipo:** ux / texto
- **Severidad:** Media (afecta la legibilidad de todas las tablas que muestran fechas — expediente, calendario, justificaciones y presumiblemente más; una familia o docente guatemalteco no está acostumbrada a leer "2015-01-01" de corrido, y el prompt maestro RNF-08 pide tono institucional claro)
- **Rol con el que ocurrió:** cualquiera que vea listados con fechas (reproducido con `dir.demo` y `guia.demo`).
- **Dónde:** varias pantallas, misma causa:
  - `/administrativo/estudiantes` — columna "Nacimiento".
  - `/administrativo/calendario` — columna "Fecha".
  - `/operativo/justificaciones` — columna "Fecha".
- **Referencia:** TRV-08 del plan. RNF-08 (tono/consistencia). No hay RF/RN que fije un formato pero el estándar de Guatemala es dd/mm/aaaa.
- **Pasos para reproducir:**
  1. Login como `dir.demo`.
  2. Abrir **Estudiantes** → observar la columna "Nacimiento".
  3. Abrir **Calendario** → observar la columna "Fecha".
  4. Abrir **Justificaciones** → observar la columna "Fecha".
- **Esperado:** las fechas se muestran como `dd/mm/aaaa` (p. ej. `01/01/2015`), consistente con cómo las escribe el personal del centro.
- **Obtenido:** las tres pantallas muestran el valor crudo que devuelve la API (ISO 8601), p. ej. `2015-01-01`.
- **Reproducible:** siempre.
- **Evidencia:** observación directa en los listados (confirmado por la tester).
- **Viewport:** escritorio y móvil 375 px (es un problema de renderizado, no de layout).
- **Hipótesis de causa (hipótesis):** las columnas usan el valor del campo sin un formateador. Ejemplos:
  - `frontend/src/features/estudiantes/components/EstudiantesPage.vue:42` → `{ clave: "birth_date", etiqueta: "Nacimiento" }` (sin `texto:` que formatee).
  - `CalendarioPage.vue` y `JustificacionesPage.vue` tienen el mismo patrón sobre `event_date` y la fecha de asistencia.
  - Faltaría un helper compartido tipo `formatearFecha(iso: string): string` que devuelva `dd/mm/aaaa` con `Intl.DateTimeFormat("es-GT", { dateStyle: "short", timeZone: "America/Guatemala" })` y aplicarlo a cada columna. Beneficio adicional: respeta la zona horaria local (relevante por B-005).
- **Nota:** el `<input type="date">` sí respeta el locale del navegador (muestra dd/mm/aaaa al usuario pero envía YYYY-MM-DD al backend), así que la asimetría es solo en los listados — los formularios están bien.

---

### B-012 · El mensaje de error cuando se sube un archivo no-xlsx filtra jerga técnica (`File is not a zip file`)

- **Caso del plan:** PLA-03 (archivo de otro tipo/vacío/enorme → errores claros)
- **Tipo:** texto / ux
- **Severidad:** Baja (el usuario sabe que algo falló, pero no entiende por qué; no bloquea el trabajo, solo deja mal el tono institucional del RNF-08)
- **Rol con el que ocurrió:** `tallerista.demo`
- **Dónde:** `/operativo/plantilla-talleres` → "Subir plantilla". API: `POST /api/v1/attendance/template/upload/`.
- **Referencia:** PLA-03 del plan; RNF-08 ("sin mensajes técnicos/en inglés"); TRV-07.
- **Pasos para reproducir:**
  1. Login como `tallerista.demo`.
  2. En Plantilla de talleres, en vez de subir un .xlsx real, subir un archivo cualquiera renombrado a `.xlsx` (p. ej. un `.txt` con texto renombrado a `.xlsx`).
- **Esperado:** mensaje institucional, p. ej. "El archivo no es un .xlsx válido. Asegurate de que sea una plantilla descargada de este mismo módulo."
- **Obtenido:** la pantalla muestra:
  ```
  La plantilla tiene errores y no se guardó ningún registro. Corregí estas filas y volvé a subirla:
  • No se pudo leer el archivo: File is not a zip file
  ```
  "File is not a zip file" es el mensaje crudo que levanta `openpyxl.load_workbook` cuando el archivo no es un xlsx — xlsx internamente es un zip, de ahí la frase. Se filtra tal cual al cliente.
- **Reproducible:** siempre.
- **Evidencia:** captura/texto del mensaje de la pantalla.
- **Viewport:** escritorio.
- **Hipótesis de causa (hipótesis):** `backend/apps/attendance/api/views.py:234` (`AttendanceTemplateUploadView.post`) tiene `except Exception as exc: raise ValidationError(f"No se pudo leer el archivo: {exc}")` que concatena el mensaje crudo del paquete. Faltaría o bien atrapar `zipfile.BadZipFile` y `openpyxl.utils.exceptions.InvalidFileException` por separado con texto humano, o devolver un genérico "El archivo no es una planilla .xlsx válida" sin exponer `exc`.

---

### B-013 · La plantilla de talleres se descarga como "plantilla.xlsx" sin la sección ni la fecha en el nombre

- **Caso del plan:** PLA-01 (nombre institucional del archivo descargado)
- **Tipo:** bug / texto
- **Severidad:** Baja (al descargar varias plantillas seguidas, el nombre no identifica cuál es cuál; una Dirección que baja plantillas de dos talleres distintos termina con dos `plantilla (1).xlsx` y `plantilla (2).xlsx`)
- **Rol con el que ocurrió:** `tallerista.demo`
- **Dónde:** `/operativo/plantilla-talleres` → "Descargar plantilla". API: `GET /api/v1/attendance/template/{section}/{fecha}/`.
- **Referencia:** no documentado como RF/RN. El plan lo pide en PLA-01 ("estructura fija") y es parte de TRV-08 (identificación clara del archivo).
- **Pasos para reproducir:**
  1. Login como `tallerista.demo` → Plantilla de talleres.
  2. Fecha `2026-11-10` (o cualquier otra). Clic "Descargar plantilla".
  3. Mirar el archivo en `Downloads/` → se llama `plantilla.xlsx`, no `asistencia_Taller_de_panaderia_2026-11-10.xlsx`.
- **Esperado:** el nombre del archivo debería ser `asistencia_<Taller>_<Fecha>.xlsx` como arma el backend en `backend/apps/attendance/api/views.py:180` (`nombre_archivo = f"asistencia_{section.grade}_{fecha}.xlsx".replace(" ", "_")`).
- **Obtenido:** el nombre queda en el fallback del frontend (`"plantilla.xlsx"`, `asistenciaApi.ts:72`) porque el regex `/filename="?([^"]+)"?/` no logra extraer un filename **válido** del header. Al inspeccionar el `Content-Disposition` del backend con `curl -D -`, el header llega así:
  ```
  Content-Disposition: attachment; filename="asistencia_Taller_de_panader\xef\xbf\xbda_2026-11-10.xlsx"
  ```
  La `í` de "panadería" se emite como byte malformado (U+FFFD, "replacement character"). Axios/el navegador rechaza o normaliza el header raro, y el frontend cae al fallback.
- **Reproducible:** siempre que la sección tenga un carácter no-ASCII en `grade` (acá "panadería" con `í`). Si existieran talleres sin tildes/ñ, probablemente funcionaría.
- **Evidencia:** `curl -D -` sobre `GET /api/v1/attendance/template/81ead3b6-4c4b-43c1-b2ec-5a81f632a87e/2026-11-10/` muestra el header corrupto. Pantalla descargando `plantilla.xlsx`.
- **Viewport:** no aplica (es header HTTP + descarga).
- **Hipótesis de causa (hipótesis):** `backend/apps/attendance/api/views.py:180-182` arma el `Content-Disposition` concatenando el `grade` tal cual en una f-string sobre un HTTP header. Los headers HTTP son ASCII por defecto; cualquier carácter fuera de ASCII tiene que codificarse con RFC 5987 (`filename*=UTF-8''...`). Faltaría usar `urllib.parse.quote` o Django `escape_uri_path`, o emitir:
  ```python
  from urllib.parse import quote
  nombre_ascii = unicodedata.normalize("NFKD", nombre_archivo).encode("ascii", "ignore").decode()
  respuesta["Content-Disposition"] = (
      f'attachment; filename="{nombre_ascii}"; '
      f"filename*=UTF-8''{quote(nombre_archivo)}"
  )
  ```
  El mismo patrón probablemente afecte a los demás documentos descargables con tildes en el nombre (constancias, boletines) — vale revisar.

---

### B-014 · RN-12 ("falta sin justificar quita el derecho a actividades del día") existe en el dominio pero no se refleja en ninguna pantalla

- **Caso del plan:** ASI-10
- **Tipo:** falta-funcionalidad
- **Severidad:** Media (la regla está declarada en el prompt maestro como regla de negocio, pero no llega al usuario: ni la familia, ni la Dirección, ni el docente ven que un estudiante perdió el derecho a actividades por falta sin justificar; en la práctica el estudiante podría presentarse al taller/actividad porque nadie se lo niega visualmente)
- **Rol con el que ocurrió:** `guia.demo` (operativo) y `familia.demo` (portal). Reproducido en ambos.
- **Dónde:** `/operativo/tomar-asistencia`, `/operativo/justificaciones`, portal de familia (asistencia).
- **Referencia:** RN-12 del prompt maestro ("Una falta sin justificar quita el derecho a las actividades del día; la justificación se evalúa según el caso, nunca automática"). Plan: ASI-10.
- **Pasos para reproducir:**
  1. Como `guia.demo`, marcar a un estudiante como **Ausente** en una fecha (sin crear justificación).
  2. Abrir el portal como `familia.demo`, ir al estudiante → pantalla de Asistencia.
  3. Buscar en la UI (vista del día, lista de ausencias, calendario del día): ¿aparece algún indicador tipo "sin derecho a actividades hoy"?
- **Esperado:** una marca/badge/mensaje visible al rol que corresponda (al menos a Dirección y a la familia; probablemente también al docente de taller cuando lista a sus participantes del día). Un simple badge rojo "No participa de actividades hoy" sobre el nombre bastaría.
- **Obtenido:** la UI muestra solo el estado de la asistencia (`ausente`, `presente`, `tarde`, `justificado`). No hay ningún indicador que derive de RN-12. Un estudiante con falta sin justificar se ve exactamente igual que uno sin registro.
- **Reproducible:** siempre.
- **Evidencia:** observación directa en el portal de familia confirmada por la tester.
- **Viewport:** escritorio y móvil 375 px.
- **Hipótesis de causa (hipótesis):** la lógica existe pero está desconectada.
  - `backend/apps/attendance/domain/rights.py` define `pierde_derecho_a_actividades(status, tiene_justificacion_aprobada) -> bool`, pero **ningún lugar** del backend la invoca (grep confirma: solo su propio test `test_rn12_pierde_derecho.py`). No hay un campo derivado en `AttendanceSerializer`, no se pasa al portal, no se usa para filtrar la vista del taller.
  - Lo mínimo para cerrar la regla: agregar un `SerializerMethodField` en `AttendanceSerializer` llamado `pierde_derecho_hoy` o similar, calculado con `pierde_derecho_a_actividades(obj.status, obj.justifications.filter(resolution="aprobada").exists())`, y mostrarlo en la UI de asistencia (como badge) y en la lista del taller del día (bloquear/avisar al tallerista).

---

### B-016 · En móvil 375 px, el botón "✕" para quitar una clase del horario desaparece cuando el nombre del curso es largo

- **Caso del plan:** HOR-04 ("Mover/editar/eliminar una clase | Se actualiza") + TRV-01 (móvil 375 px)
- **Tipo:** ux
- **Severidad:** Media (en un teléfono — flujo probable para la Dirección — no se puede quitar una clase con nombre largo como "Comunicación y lenguaje L1"; obliga a cambiar de dispositivo)
- **Rol con el que ocurrió:** `dir.demo` (único rol con `editar` en horarios).
- **Dónde:** `/administrativo/horario` en viewport móvil 375 px.
- **Referencia:** RNF-01 (móvil usable), HU-06 (editar horario), TRV-01.
- **Pasos para reproducir:**
  1. Login como `dir.demo` → Horario.
  2. DevTools F12 → modo responsive 375 × 667.
  3. Agregar o localizar una celda con un curso de nombre largo (p. ej. "Comunicación y lenguaje L1" en 1°A).
  4. Observar la celda: aparece el nombre del curso ocupando todo el ancho.
- **Esperado:** la "×" siempre visible junto al nombre, o el nombre se trunca con `text-overflow: ellipsis` para dejar lugar al botón, o la "×" queda a la izquierda/arriba fuera del scroll horizontal del nombre.
- **Obtenido:** la "×" queda detrás del texto (o fuera de la celda), fuera de alcance táctil. Confirmado por la tester "cuando el nombre del curso es muy largo no aparece la x para eliminar, esto lo veo siempre desde la resolución de pantalla de celular".
- **Reproducible:** siempre con cursos de nombre largo + viewport móvil.
- **Evidencia:** observación directa de la tester (reproducido en DevTools móvil 375 px con la celda "Comunicación y lenguaje L1").
- **Viewport:** móvil 375 px. En escritorio la "×" sí se ve.
- **Hipótesis de causa (hipótesis):** `frontend/src/features/horarios/components/HorarioGridPage.vue:306-316` (`.horario-grid__celda--ocupada`) usa `display: flex; justify-content: space-between` con el nombre antes y la "×" después; el texto largo empuja a la "×" fuera del contenedor porque la celda tiene `padding` fijo pero el ancho mínimo de la columna (`min-width: 40rem` en la tabla y 5 columnas) es insuficiente en 375 px. Opciones:
  - `.horario-grid__celda--ocupada > span { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }` + `.horario-grid__quitar { flex: none; }`.
  - O apilar vertical en viewport angosto (`flex-direction: column`).
  - O usar el gesto largo-tap para abrir un menú con "Quitar".

---

### B-017 · El calendario del portal de familia no permite navegar entre semanas

- **Caso del plan:** CAL-03 ("Navegación semana/mes, hoy, cambio de mes en bordes") + CAL-04 (calendario como primera pantalla)
- **Tipo:** falta-funcionalidad / ux
- **Severidad:** Media (una familia que quiere ver el horario o eventos de la próxima semana — p. ej. para planificar un viaje o preparar materiales — no puede; está anclada a la semana en curso, lo cual limita bastante el valor del portal como herramienta de planificación)
- **Rol con el que ocurrió:** `familia.demo`.
- **Dónde:** portal de familia, primera pantalla (`/portal` o similar, el `WeeklyCalendarView` que arma el componente).
- **Referencia:** RF-28 (calendario semanal como primera pantalla); CAL-03 del plan.
- **Pasos para reproducir:**
  1. Login como `familia.demo`.
  2. Observar la primera pantalla: aparece un calendario con los 5 días de la semana en curso y los eventos del día.
  3. Buscar botones "←" / "→" o similares para cambiar de semana.
- **Esperado:** botones "Semana anterior / Semana siguiente / Hoy" (al estilo de un calendario); al clickear "siguiente", la vista avanza 7 días; "Hoy" vuelve al presente. Idealmente también un selector de mes.
- **Obtenido:** no hay navegación: la vista muestra solo la semana en curso. Para ver otro día hay que esperar a que llegue.
- **Reproducible:** siempre.
- **Evidencia:** confirmación de la tester "no muestra semana a semana".
- **Viewport:** confirmado en móvil 375 px; probablemente igual en escritorio (misma pantalla).
- **Hipótesis de causa (hipótesis):** el backend `WeeklyCalendarView` (`backend/apps/scheduling/api/views.py:181-258`) devuelve TODOS los `schedule_blocks` y `calendar_events` de las secciones del estudiante — no filtra por semana. Así que la data está, el frontend decide qué pintar. En el componente del portal (probablemente `frontend/src/features/portal/components/*.vue` que arma el calendario semanal) hace falta:
  - Un estado reactivo `semanaRef` con la fecha de inicio de la semana que se muestra.
  - Botones "←", "→", "Hoy" que modifican `semanaRef`.
  - El cálculo de qué eventos pintar en cada día filtra por `event.event_date` contra la semana activa.
  - Idealmente también cambiar `WeeklyCalendarView` para aceptar un parámetro `?week=YYYY-MM-DD` y devolver solo esa ventana (reduce el payload cuando el ciclo tiene muchos eventos).

---

### B-018 · `DELETE /students/`, `/guardians/`, `/enrollments/` hace hard-delete en vez de baja lógica

- **Caso del plan:** EST-08 ("Editar/desactivar estudiante | No se borra; sale de listas activas, sigue en históricos")
- **Tipo:** bug / seguridad / datos
- **Severidad:** Alta (pérdida de datos irreversible y violación directa de HU-02 + sección 8.5 del prompt maestro — "un registro maestro en uso se desactiva, no se elimina", "nothing is ever hard-deleted"; hoy no hay botón UI que dispare esto, pero el endpoint REST está vivo y cualquier `curl` o integración lo borra físicamente, perdiendo histórico de asistencia, notas y pagos si no están protegidos por FK)
- **Rol con el que ocurrió:** `dir.demo` (cualquiera con `editar` en `estudiantes_encargados`).
- **Dónde:** API — `DELETE /api/v1/students/{public_id}/`, `DELETE /api/v1/guardians/{public_id}/`, `DELETE /api/v1/enrollments/{public_id}/`.
- **Referencia:** HU-02 (baja lógica), sección 8.5 del prompt maestro, `CLAUDE.md` ("Nothing is ever hard-deleted — `is_active=False` via `BajaLogicaMixin` or a custom `perform_destroy`"). Plan: EST-08.
- **Pasos para reproducir:**
  1. `curl` o `Invoke-RestMethod` como `dir.demo`.
  2. Crear un estudiante nuevo: `POST /api/v1/students/` con datos válidos. Guardar `public_id`. Ejemplo probado: `512336a2-c841-4579-a5bc-7c31a16dd781` (`ES014`, "Baja Logica").
  3. `DELETE /api/v1/students/{public_id}/` → **204 No Content**.
  4. `GET /api/v1/students/{public_id}/` → **404 "No Student matches the given query."**
  5. `GET /api/v1/students/` → `count` bajó en 1; el estudiante **no está** en el listado ni como `is_active=False`.
- **Esperado:** `DELETE` responde 204 (o 200) pero el registro **permanece en la base con `is_active=False`**. `GET` del detalle debería seguir devolviendo el objeto (incluido en históricos y auditoría), y `GET /students/` sin filtros debería listarlo con `is_active=false` para que el frontend lo oculte en su propia capa (como ya hace `EstudiantesPage.vue:65-66` con secciones y becas).
- **Obtenido:** el registro desaparece físicamente de la base. Confirmado con `count` antes/después y 404 en el detalle.
- **Reproducible:** siempre.
- **Evidencia:**
  - `POST /students/` → 201 con `ES014`.
  - `DELETE /students/512336a2.../` → 204.
  - `GET /students/512336a2.../` → 404 "No Student matches the given query."
  - `GET /students/` → count 14 → 13.
- **Viewport:** no aplica (API).
- **Hipótesis de causa (hipótesis):** `backend/apps/students/api/views.py:43,96,159` — ninguno de `StudentViewSet`, `GuardianViewSet`, `EnrollmentViewSet` incluye `BajaLogicaMixin` en su lista de bases. Como `ModelViewSet.perform_destroy` por defecto hace `instance.delete()` (hard delete), caen a eso. Fix: agregar `BajaLogicaMixin` (de `apps.core.api.mixins:34-41`) a los tres, mismo patrón que ya usan `AttendanceViewSet`, `SectionViewSet`, `CalendarEventViewSet`, `TeacherAssignmentViewSet`, etc.
- **Observación cruzada:** incluso con el fix, hay registros maestros protegidos por FK (`on_delete=models.PROTECT` desde Enrollment → Student, Attendance → Enrollment, etc.). Si en el futuro se agrega un botón de "Desactivar" en la UI, hay que confirmar que la baja lógica es siempre posible aunque exista actividad vinculada (que es justamente el escenario de HU-02).

---

### B-019 · El portal de familia muestra spinner infinito (y sin mensaje) cuando el encargado no tiene estudiantes vinculados

- **Caso del plan:** EST-09 ("Encargado sin estudiantes, estudiante sin encargado | Se maneja sin romper")
- **Tipo:** bug / ux
- **Severidad:** Alta (es exactamente el estado "cuenta nueva" del flujo real del centro: la Dirección crea una cuenta de familia y le pide que entre a verificar antes de vincular estudiantes; esa primera entrada rompe la pantalla con un cargando que no termina, sin mensaje — la familia asume que el sistema no funciona y abandona)
- **Rol con el que ocurrió:** encargado nuevo creado recién por `dir.demo`.
- **Dónde:** portal de familia, primera pantalla (`WeeklyCalendarView`).
- **Referencia:** EST-09 del plan; TRV-02 (estado vacío debe tener mensaje útil, no una pantalla congelada).
- **Pasos para reproducir:**
  1. Login como `dir.demo` → **Encargados** → "Nuevo encargado".
  2. Crear un encargado nuevo con sus datos de contacto + usuario (**sin vincular aún a ningún estudiante**).
  3. En ventana incógnita, login con las credenciales del encargado recién creado.
  4. Observar la primera pantalla del portal de familia.
- **Esperado:** un estado vacío amable con mensaje tipo "Todavía no tenés estudiantes vinculados a esta cuenta. Pedí a la Dirección del centro que te vincule." + algún link/contacto. Lo mínimo: que no quede cargando para siempre.
- **Obtenido:** la pantalla muestra el encabezado y los tabs del portal, pero el área central queda con un **spinner que nunca termina**. No hay mensaje de error, no hay botón para reintentar, no hay texto que explique por qué no se ve nada. En Network no aparece error (confirmado por la tester).
- **Reproducible:** siempre con cualquier encargado sin `GuardianStudentLink` activo.
- **Evidencia:** observación directa de la tester; probablemente la pantalla espera un `selectedStudentId` que nunca llega porque el store de portal queda vacío, y los componentes hijos nunca entran al `v-else` del estado vacío.
- **Viewport:** confirmado en móvil y escritorio.
- **Hipótesis de causa (hipótesis):** el flujo del portal probablemente hace algo como:
  1. `authStore.me` carga el usuario.
  2. `portalStore.cargar()` pide los estudiantes vinculados a este encargado (`/students/`).
  3. Al llegar `0` estudiantes, `portalStore.studentActivo` sigue `null`.
  4. El `<CalendarioSemanaPage>` tiene `watchEffect` sobre `studentActivo` y, mientras sea `null`, no dispara `/calendar/weekly/` **pero tampoco sale del estado `cargando`** — queda en el ternario entre "cargando" y "mostrar pantalla", sin la rama "no hay estudiantes".
  5. Falta un `v-else-if="!studentActivo"` con un `<EmptyState titulo="Todavía no hay estudiantes vinculados" descripcion="..." />` arriba del `<CargandoBloque>`.
- **Pregunta de diseño:** si el flujo deseado del centro es "crear encargado y vincular en el mismo turno", podría también evaluarse exigir al menos un estudiante vinculado antes de guardar la cuenta (como validación en el servicio `crear_encargado`). Pero eso es una decisión del dueño del producto.

---

### B-020 · PATCH /assignments/ no revalida tipos — se puede asignar un Tallerista a un curso académico editando una asignación existente

- **Caso del plan:** ASG-03 (reasignar/quitar asignación con datos) + ASG-01 (reglas de tipos)
- **Tipo:** bug / datos
- **Severidad:** Media (abre la puerta a dejar asignaciones inconsistentes que violan ADR-0001; la Dirección puede cambiar el docente de "Matemática 2° básico" por un Tallerista y el sistema lo acepta, aunque ese Tallerista no debería poder recibir cursos académicos — un posterior cálculo de reportes o un acceso a asistencia desde esa asignación entra en estado inconsistente)
- **Rol con el que ocurrió:** `dir.demo`.
- **Dónde:** `PATCH /api/v1/assignments/{public_id}/`.
- **Referencia:** ADR-0001 (una asignación docente solo es válida si el tipo del curso coincide con el tipo de la sección y el rol del usuario coincide con el tipo de curso); ASG-01 del plan.
- **Pasos para reproducir:**
  1. Login como `dir.demo`.
  2. `PATCH /api/v1/assignments/82a949dc-35c3-4e52-826c-da0b3b96105f/` (asignación `Matemática` @ `Segundo básico`, teacher = `docente.demo`) con cuerpo `{"teacher": "209f99a8-17d0-4fb3-a644-778ae968584a"}` (public_id de `tallerista.demo`).
  3. Status: `200 OK`. Al releer la asignación, `teacher` quedó `209f99a8` (tallerista). El curso sigue siendo `Matemática` (académico). Un Tallerista enseñando Matemática.
- **Esperado:** el `PATCH` ejecuta la misma validación que el `POST`: `validar_asignacion(course_type="academico", section_type="academica", teacher_role_name="Tallerista")` lanza `AsignacionInvalida` → la vista devuelve `400 Bad Request` con mensaje "El rol 'Tallerista' no puede asignarse a un curso de tipo 'academico'" (igual que confirma el test de ASG-01).
- **Obtenido:** la validación solo corre en `TeacherAssignmentViewSet.perform_create` (`backend/apps/scheduling/api/views.py:64-68`), no en `perform_update`. El `PATCH` escribe directamente sin pasar por `validar_asignacion`.
- **Reproducible:** siempre.
- **Evidencia:**
  - `PATCH {teacher: tallerista.demo}` → 200 con `course_name: "Matemática"` + `teacher: 209f99a8…` (tallerista).
  - `PATCH` revertido durante el test para no dejar el estado roto para el resto de la sesión.
- **Viewport:** no aplica (API).
- **Hipótesis de causa (hipótesis):** `TeacherAssignmentViewSet` tiene `perform_create` que llama a `crear_asignacion` (que corre la validación), pero no define `perform_update`, así que DRF usa el default `serializer.save()` que no llama a ninguna lógica de dominio. Fix: agregar un `perform_update(self, serializer)` que llame a una función `actualizar_asignacion(instance, **data)` en `scheduling/services/teacher_assignment.py`, que ejecute `validar_asignacion` antes de guardar los cambios. Alternativamente, mover la validación al método `validate` del serializer (que corre en create y update).

---

### B-021 · El horario acepta dos cursos distintos en la misma sección, mismo día y mismo período

- **Caso del plan:** HOR-03
- **Tipo:** falta-funcionalidad / datos
- **Severidad:** Media (un estudiante de 1°A puede terminar con dos clases simultáneas — Ciencias naturales y Educación física el lunes P1 — y el calendario semanal del portal familia muestra las dos; nada en el sistema impide armar un horario físicamente imposible)
- **Rol con el que ocurrió:** `dir.demo`.
- **Dónde:** `POST /api/v1/schedule-blocks/`.
- **Referencia:** no documentado como RN/HU (HU-06 solo norma el choque del mismo docente, no el choque de sección). HOR-03 del plan.
- **Pasos para reproducir:**
  1. En 1°A ya hay un bloque Lunes P1 asociado a la asignación `b8f7ca4c-...` (teacher `b6c7ed98` = `guia.demo`, curso Ciencias naturales).
  2. Login como `dir.demo` → POST `/api/v1/schedule-blocks/` con `{"assignment":"68efc052-9a2e-4867-95c2-462dc3438f8f","day_of_week":"lunes","period_number":1}` — esa asignación es también de 1°A pero con otro docente (`67b02934`) y curso Educación física.
- **Esperado:** `400 Bad Request` con mensaje tipo "Esta sección ya tiene una clase en el lunes, período 1 (<Ciencias naturales>)". El bloque no se crea.
- **Obtenido:** `201 Created`. El nuevo bloque `337e2aa3-...` convive con el existente `b8f7ca4c-...` en el mismo horario y la misma sección, con docentes distintos. (Limpié el bloque de prueba al final del test.)
- **Reproducible:** siempre.
- **Evidencia:** `POST /schedule-blocks/` → 201; `GET /schedule-blocks/` listando ambos bloques en lunes P1 vinculados a asignaciones de la misma sección `3afe8e63-...`.
- **Viewport:** no aplica (API; la UI de `HorarioGridPage.vue` también acepta el flujo).
- **Hipótesis de causa (hipótesis):** `backend/apps/scheduling/services/schedule_block.py:16-30` (`crear_bloque`) hace `.filter(assignment__teacher=…, day_of_week=…, period_number=…).exclude(assignment=…).exists()` — solo chequea el docente. Falta el chequeo paralelo:
  ```python
  hay_cruce_de_seccion = (
      ScheduleBlock.objects
      .filter(assignment__section=assignment.section, day_of_week=day_of_week,
              period_number=period_number, is_active=True)
      .exclude(assignment=assignment)
      .exists()
  )
  if hay_cruce_de_seccion:
      raise CruceDeHorario(f"La sección {assignment.section} ya tiene una clase el {day_of_week} en el período {period_number}.")
  ```

---

### B-015 · La grilla de Horario no muestra el receso entre P3 y P4

- **Caso del plan:** HOR-01 ("Grilla: 6 períodos de 40 min + receso | Estructura correcta")
- **Tipo:** ux / falta-funcionalidad
- **Severidad:** Baja (cosmético; la grilla sigue siendo funcional, pero una Dirección que arma el horario ve un salto raro entre `P3 09:20–10:00` y `P4 10:40–11:20` sin explicación visual del receso, lo cual puede confundir)
- **Rol con el que ocurrió:** `dir.demo` (reproducible con cualquiera que acceda a la grilla).
- **Dónde:** `/administrativo/horario`.
- **Referencia:** RN-13 ("La jornada tiene seis períodos de 40 minutos y un receso de la misma duración") y HOR-01 del plan.
- **Pasos para reproducir:**
  1. Login como `dir.demo` → Horario.
  2. Elegir cualquier docente en el selector.
  3. Mirar la grilla: filas P1, P2, P3, P4, P5, P6 — no hay fila "Receso 10:00–10:40" entre P3 y P4.
- **Esperado:** una fila "Receso 10:00–10:40" entre P3 y P4, visualmente distinta (p. ej. en gris, sin celdas clickeables), que haga explícito el bloque descanso que define RN-13.
- **Obtenido:** la grilla salta de P3 (09:20–10:00) a P4 (10:40–11:20) sin fila intermedia. El salto de 40 minutos queda implícito solo en los horarios dentro del encabezado de cada fila.
- **Reproducible:** siempre.
- **Evidencia:** confirmación visual de la tester.
- **Viewport:** escritorio y móvil 375 px (mismo CSS).
- **Hipótesis de causa (hipótesis):** `frontend/src/features/horarios/api/horariosApi.ts:30-37` define `PERIODOS` con solo los 6 períodos lectivos y el componente `HorarioGridPage.vue` itera `v-for="periodo in PERIODOS"`. Para cerrar la regla alcanza con intercalar una fila especial entre `periodo.numero === 3` y `periodo.numero === 4` que no acepte celdas (o un item sintético en `PERIODOS` con `tipo: "receso"` que el template renderice sin la lógica de clickear).

---

### B-005 · "Tomar asistencia" preselecciona la fecha de mañana cuando el usuario entra después de las 6pm local

- **Caso del plan:** TRV-08 (zona horaria de Guatemala)
- **Tipo:** bug / datos
- **Severidad:** Media (los primeros registros del docente, hechos de buena fe sin cambiar el input, quedan con la fecha equivocada: "pasé lista hoy a las 7:30 pm" aparece registrado al día siguiente)
- **Rol con el que ocurrió:** `guia.demo` (rol "Docente con sección a cargo")
- **Dónde:** `/operativo/tomar-asistencia`.
- **Referencia:** TRV-08 del plan ("zona horaria de Guatemala, UTC-6"). RNF-08 (consistencia). No hay RN explícito.
- **Pasos para reproducir:**
  1. Confirmar que la computadora está en zona horaria de Guatemala (UTC-6). Esperar o ajustar el reloj a cualquier hora **igual o posterior a 18:00 local** (en este caso real: 23:35 local).
  2. Login como `guia.demo` → **Tomar asistencia**.
  3. Sin tocar el campo **Fecha**, hacer clic en "Presente" de un estudiante.
  4. Mirar la respuesta del `POST /api/v1/attendance/`.
- **Esperado:** el input "Fecha" tiene como valor por defecto la fecha **local** del día (p. ej. `2026-10-06` si en Guatemala son las 23:35 del 6/10), y la asistencia queda registrada ese día.
- **Obtenido:** con hora local **23:35 del 2026-10-06**, el input quedó en `2026-10-07` y la asistencia se grabó con `"date": "2026-10-07"`:
  ```json
  {
    "public_id": "febc41b7-e5eb-4820-bd43-cc8fb9b2ccab",
    "enrollment": "c18bef8f-78b6-4e3b-8f89-c94d85586980",
    "date": "2026-10-07",
    "status": "presente",
    "source": "manual",
    "recorded_by": "guia.demo",
    "section_type": "academica",
    "is_active": true
  }
  ```
  Guatemala es UTC-6, así que a las 23:35 local ya son las 05:35 del día siguiente en UTC — y el input tomó la fecha de UTC.
- **Reproducible:** siempre entre las 18:00 y las 23:59 locales (ventana de 6 horas cada noche).
- **Evidencia:** respuesta JSON de arriba. Hora local al momento del registro: 23:35, 2026-10-06.
- **Viewport:** escritorio (es un cálculo de JS, idéntico en móvil 375 px).
- **Hipótesis de causa (hipótesis):** `frontend/src/features/asistencia/components/TomarAsistenciaPage.vue:27` arma la fecha por defecto con `new Date().toISOString().slice(0, 10)`. `toISOString` siempre devuelve UTC, no la hora local, así que entre las 18:00 y las 23:59 Guatemala el resultado es la fecha del día siguiente. Lo correcto para una fecha "de hoy local" es algo como `new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Guatemala' }).format(new Date())` o `new Date().toLocaleDateString('sv-SE')` (que ya usa el huso local). **Misma causa** aparece en `PlantillaAsistenciaPage.vue:27` y en `EstudiantesPage.vue:107` (`enrolled_at: new Date().toISOString().slice(0, 10)`) — probable misma raíz que posibles hallazgos futuros en esas pantallas; chequear por aparte si tiene impacto visible en producción.


---

## Cobertura de mi set

Marca cada caso: ✅ pasó · ❌ falló (ver hallazgo) · ⏭️ no se pudo probar (por qué)

| Caso | Estado | Hallazgo(s) |
|---|---|---|
| EST-01 | ✅ | — (código `internal_code` asignado por el sistema, no editable, consecutivo) |
| EST-02 | ✅ | — (misma sección y segunda sección académica mismo ciclo → 400) |
| EST-03 | ❌ | B-002 |
| EST-04 | ✅ | — (con seed_masivo: 71 estudiantes agrupados en páginas de 25 client-side, búsqueda cliente sobre el total; `shared/api/resource.ts` sigue `next` con `page_size=200`) |
| EST-05 | ✅ | — (sensitive: dir 200/200, admin 200/403, resto 403/403) |
| EST-06 | ✅ | — (encargado + usuario en un solo paso; contraseña elegida por admin; vinculación es paso aparte) |
| EST-07 | ✅ | — (vincular + desvincular funciona; UniqueConstraint sobre (guardian, student) correcto) |
| EST-08 | ❌ | B-018 (hard delete); editar sí funciona (TRV-05) |
| EST-09 | ❌ | B-019 (familia sin hijos → spinner infinito) |
| ASG-01 | ✅ | — (tipos cruzados Docente↔taller y curso↔sección → 400 con mensaje claro) |
| ASG-02 | ✅ | — (asignación duplicada → 400 "deben formar un conjunto único") |
| ASG-03 | ❌ | B-020 (PATCH no revalida tipos); DELETE con bloques → 500 (ver Cosas raras ProtectedError) |
| ASG-04 | ✅ | — (docente/guía/tallerista ven solo las suyas; coord/dir/admin ven todas) |
| HOR-01 | ❌ | B-015 |
| HOR-02 | ✅ | — (mismo docente, mismo día+período → 400 con mensaje claro) |
| HOR-03 | ❌ | B-021 |
| HOR-04 | ❌ | B-016 (en móvil) · ✅ en escritorio (propaga a Mi horario) |
| HOR-05 | ✅ | — (coord 403 en POST /schedule-blocks/) |
| CAL-01 | ✅ | — (edición respetada RN-17; ver también B-009 por el gap de lectura cross-docente) |
| CAL-02 | ❌ | B-003 |
| CAL-03 | ❌ | B-017 (no hay navegación semana a semana en el portal) |
| CAL-04 | ✅ | — (primera pantalla del portal es calendario semanal con horario del hijo y selector de hijos) |
| ASI-01 | ✅ | — (4 estados persisten; nota de F5 en Cosas raras) |
| ASI-02 | ✅ | ver "Cosas raras" |
| ASI-03 | ✅ | — (durante clase vía hora de llegada + al final por botón conviven) |
| ASI-04 | ✅ | — (PATCH asistencia existente → 200; ver nota en Cosas raras sobre edición post-justificación) |
| ASI-05 | ❌ | B-004, B-005 |
| ASI-06 | ⏭️ | — (retirar/graduar/trasladar fuera de alcance en fase actual — ver Cosas raras) |
| ASI-07 | ✅ | — (Dirección POST /attendance/ → 201, sin requerir asignación docente) |
| ASI-08 | ✅ | — (tallerista 0; coord/admin/dir ven todas; docentes limitados a sus secciones — probado por API con datos sembrados) |
| ASI-09 | ❌ | B-007 |
| ASI-10 | ❌ | B-014 |
| JUS-01 | ✅ | — (POST /justifications/ 201 pendiente, verificado en B-006 y T4) |
| JUS-02 | ✅ | — (403 para guia/docente/coord confirmado por API) |
| JUS-03 | ❌ | B-008 (y ✅ para la parte de "aprobar → justificado") |
| JUS-04 | ❌ | B-006 (duplicados); rango cruza ciclos ⏭️ (modelo asocia justificación a UNA asistencia, no a un rango) |
| PLA-01 | ❌ | B-013 (nombre del archivo); nota: plantilla no protegida (ver Cosas raras) |
| PLA-02 | ✅ | — (carga válida → 2 asistencias registradas) |
| PLA-03 | ❌ | B-012 (mensaje jerga técnica); código inválido y estado inválido se reportan bien |
| PLA-04 | ❌ | B-001 |
| PLA-05 | ✅ | — (misma plantilla dos veces: segunda falla con mensaje claro, nada se duplica) |

## Cosas que me parecieron raras pero no estoy seguro de que sean error

- **Borde de RN-11 (ASI-02).** Según el código (`backend/apps/attendance/domain/late_arrival.py:15`, `hora_llegada <= time(8, 5)`), el minuto 05 cuenta como presente y el 06 ya es tarde. Confirmado en pantalla: 07:59 y 08:05 → "presente"; 08:09 y 08:30 → "tarde". El prompt maestro dice "pasados cinco minutos de las ocho de la mañana el estudiante queda tarde" (RN-11, pág. 11), que es ambiguo entre "a partir del minuto 05" y "a partir del 06". El centro debería confirmar; no es bug, pero conviene fijar el criterio por escrito.
- **UX del campo "o la hora de llegada" en Tomar asistencia.** Fue difícil escribir la hora a mano con teclado numérico; terminé usando el reloj del picker nativo. Si al docente se le complica tipear directo (uno de los flujos esperados en una sección de 20+ estudiantes), vale la pena revisar que el input quede con `step="60"` explícito y buena guía (`placeholder`/`aria-label`) para que el teclado dé respuesta inmediata. No es bug.
- **El input "Fecha" de Tomar asistencia volvió a mostrar el día siguiente** en cada apertura hecha después de las 6 pm local. Mismo bug ya anotado como B-005; lo documento acá como corroboración adicional (ocurrió con registros fechados 2026-10-08 y 2026-10-09 en pruebas hechas el 06 y 07 por la noche).
- **Sección inactiva sigue listada por `GET /sections/`** (confirmado tras un `DELETE /sections/{id}/` que hace baja lógica a `is_active=False`). Varios paneles del frontend filtran por `is_active !== false` del lado del cliente (`EstudiantesPage.vue:65`), pero otros no (`TomarAsistenciaPage.vue:91-93` para los roles con área `datos_maestros` carga `secciones.value` sin filtrar). Posible que CAT-02 (Set A) detecte secciones inactivas apareciendo en selectores nuevos. Baja; levantar con Francisco si lo encuentra.
- **La API acepta crear asignaciones y bloques de horario en secciones inactivas** (sin ponerla previamente de vuelta en activo). Hice `DELETE /sections/{Cuarto bachillerato}` → `is_active=False`; después `POST /assignments/` apuntando a esa sección → `201 Created`. Si el centro desactiva una sección para dejar de usarla, aún así se puede agregar personal — probablemente no es lo que quiere.
- **`PATCH /sections/{id}/ {"is_active": false}` responde 200 pero no actualiza `is_active`.** El campo quedó marcado como `read_only` o filtrado por el serializer, pero no devuelve error — el cliente cree que apagó la sección y en realidad sigue activa. Debería o bien 400 (campo no editable) o aceptar el cambio.
- **`DELETE /assignments/{id}` lanza 500 si queda un `CalendarEvent` apuntando a esa asignación, aun cuando el evento ya está dado de baja lógica (`is_active=False`).** El `on_delete=PROTECT` dispara `ProtectedError` sin manejar, se vuelve 500 crudo. Problema general del patrón de bajas lógicas con FKs PROTECT; conviene atraparlo y devolver 409 con un mensaje tipo "No podés quitar la asignación porque todavía hay un evento (dado de baja o no) que la referencia."
- **El filtro `?is_active=true` en `/sections/` no aplica** — con 1 sección inactiva en la base, `GET /sections/?is_active=true&page_size=100` devolvió los 7 registros (count=7). El query param no está wired al `filter_backends` del viewset.
- **ACC-07 (Set A).** Durante los tests de TRV-03 descubrí que después de ~15 min de inactividad, cualquier click (p. ej. "Inscribir") devuelve 401 `Token is expired` en Network, y el frontend no renueva automáticamente ni muestra mensaje. El usuario simplemente ve que "nada pasa" tras clickear un botón. Debería activarse el refresco silencioso con la cookie de refresh. Reportar a Francisco (Set A) — es el caso ACC-07 que él tiene que cerrar.
- **Fricción teclado en `<input type="date">`** (TRV-11). En los formularios con campo de fecha (Inscribir estudiante, Publicar evento, etc.), el input solo deja ingresar la fecha con el calendario; no permite tipear día/mes/año con el teclado numérico. Chrome *técnicamente* soporta tipeo si uno clickea en la sub-parte del input (día, luego Tab/flecha a mes, etc.), pero en la práctica el usuario común no lo descubre. Baja/UX; podría mejorarse con un hint o adoptando un `<input type="text">` con validación.
- **La plantilla de talleres descargada no tiene protección de celdas** (PLA-01, HU-19/20). El xlsx se abre completamente editable: código y nombre se pueden cambiar libremente desde Excel antes de volver a subirlo. El backend valida códigos al subir (confirmado en B-012 variante A — "El código ES999 no pertenece a esta sección"), así que la manipulación no logra meter datos basura, pero la promesa literal de HU-19/20 ("Los códigos y la estructura no se pueden modificar") no se cumple. Baja; se cierra con `openpyxl.worksheet.protection.SheetProtection` sobre las columnas A y B.
- **Tomar asistencia: F5 pierde el contexto de sección y fecha** (ASI-01). El estado de los filtros (sección elegida, fecha) vive solo en memoria del componente; al recargar vuelve a la fecha por defecto y a la primera sección disponible. Los datos guardados persisten (si se vuelve a la combinación anterior, siguen marcados), pero el usuario pierde el "¿dónde estaba?" cada vez que recarga. Baja/UX; se cierra guardando sección+fecha en la URL (`?seccion=…&fecha=…`) con `router.replace()` cada vez que cambian — y entonces F5 preserva el contexto y el link al expediente del día es compartible.
- **No hay forma de abrir el expediente del estudiante desde Tomar asistencia** (ASI-10 periferia). El nombre no es clickeable; el único acceso al expediente está desde Estudiantes del portal administrativo. Para un docente que necesita ver notas o historial de un alumno en el mismo flujo de pasar lista, hoy requiere cambiar de pantalla (o pedírselo a Dirección si el docente ni accede al admin). Baja/UX.
- **ASI-06 fuera de alcance en esta fase.** El modelo `Enrollment` tiene estados `activo/retirado/graduado/trasladado`, pero el serializer marca `status` como read-only con nota: "los cambios de estado (retiro, graduación, traslado) no están en el alcance de RF-03 todavía". Por lo tanto no se puede probar que un estudiante retirado desaparezca de los listados — porque no se puede retirar. Pendiente de un RF futuro.
- **USR-01 (Set A).** EST-06 pide "contraseña temporal una vez, obliga a cambiarla en el primer ingreso". En el formulario "Nuevo encargado" la contraseña la **escribe la Dirección** al crear la cuenta (no se autogenera), y no hay forzado de cambio en el primer login — el encargado puede seguir usando esa contraseña indefinidamente. Es responsabilidad de Francisco (USR-01, USR-05); lo documento acá porque lo cruzado con EST-06.
- **El formulario de "Nuevo encargado" no tiene campo de correo electrónico.** El `User` del centro tiene `email` opcional por diseño, pero en "Mi cuenta" aparece "sin correo registrado" visible — y no hay forma de agregarlo después tampoco desde el portal familia. Puede ser diseño (el centro no usa email para contactar), pero vale confirmar con el dueño. Baja/UX.
- **No hay vista "encargados de un estudiante" desde el expediente** (EST-07 periferia). Hoy, para saber qué encargados tiene un estudiante, hay que ir a Encargados y mirar los vínculos de cada uno — no al revés. Falta un listado inverso en `ExpedientePage.vue` que muestre los `guardian_links` activos del estudiante y permita vincular/desvincular desde ahí. Baja/UX.
