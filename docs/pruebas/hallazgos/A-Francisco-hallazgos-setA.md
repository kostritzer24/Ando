# Hallazgos — Set A — Francisco

Fecha: 2026-10-06 · Rama/commit probado: `fase-15-formatos-institucionales @ 1f92784` · Navegador: Google Chrome (canal estable, headless) · SO: Fedora Linux 44

**Entorno:** repo local `/home/javier/Ando` en la rama `fase-15-formatos-institucionales`, SQLite reseteada (`rm db.sqlite3 && migrate && seed_demo && seed_masivo`), backend en `http://localhost:8000` y frontend Vite en `http://localhost:5173` (se entró siempre por `localhost`, nunca por `127.0.0.1`). Datos de siembra: 60 estudiantes, 10 080 notas, 355 pagos, 180 boletines, usuarios extra `docente.01..06` y `familia.01..` (contraseña `CambiaEstaClave2026`).

**Nota sobre el árbol de trabajo:** quedan dos cambios locales **preexistentes** que no afectan las pruebas y no se tocaron durante el QA: `frontend/vite.config.ts` (se añadió `server.allowedHosts` para túneles de Cloudflare) y `backend/config/settings/tunnel.py` (sin trackear). El `frontend/.env` apunta a `http://localhost:8000/api/v1`.

**Datos de prueba creados durante el QA** (quedan en la SQLite; se borran con un reset de semilla): usuarios `qa.rol.*`, `qa.ui.*`, `qa.tildes`, `qa.doble.*`; 1 pago (recibo `QA-…`), 1 asistencia (2026-10-07/08), 1 nota (8.50), 1 bloque de horario (jueves, período 5, Segundo básico), 1 constancia de solvencia (`1D9126CB4204`); ciclos 2098/2099 y secciones "QA …" **dados de baja** (soft-delete), visibles en la API por diseño pero ocultos en el frontend.

**Evidencia:** `/home/javier/Descargas/QA-setA-evidencias/` (JSON por prueba + capturas PNG).

---

### A-001 · El portal de familias puede listar estudiantes insolventes de OTRAS familias (fuga de datos)

- **Caso del plan:** `PER-04` (alcance de datos por rol, probado a nivel API)
- **Tipo:** seguridad
- **Severidad:** **Crítica**
- **Rol con el que ocurrió:** `familia.demo`
- **Dónde:** `GET /api/v1/reports/insolvent-students/` (el botón "Reporte de estudiantes insolventes" existe en `/administrativo/pagos`; el portal de familia no muestra botón, pero la API responde al token de familia)
- **Referencia:** RNF-04; `docs/permisos-roles.md` (nota 3, "una familia solo sus vinculados"; nota 8, área `pagos_solvencia`)
- **Pasos para reproducir:**
  1. Iniciar sesión con `familia.demo` (`CambiaEstaClave2026`) y copiar el token de acceso.
  2. `GET http://localhost:8000/api/v1/reports/insolvent-students/` con `Authorization: Bearer <token>`.
  3. Comparar la respuesta con los estudiantes vinculados a esa familia.
- **Esperado:** 403 (la familia no tiene por qué ver el consolidado institucional de insolvencia) o, como mínimo, solo sus propios hijos acotados (RNF-04).
- **Obtenido:** 200 con **22 filas y 100 % ajenas**: ES042 Paula Batz López (Cuarto bachillerato), ES028 Daniela Batz Tzul (Segundo básico), ES011 Mishel Castillo Cumes (Primero básico A), ES021 Axel Choc Ramírez (Primero básico B), ES034 Renata Choc Reyes (Tercero básico), ES023 Sofía Coc Sánchez… Ninguna fila corresponde a los hijos de `familia.demo`. Incluye código interno, nombre, sección y meses pendientes.
- **Reproducible:** siempre
- **Evidencia:** `A-001-leak-insolventes-familia.json` (status 200, 22 filas, 0 hijos propios en la lista, 8 primeros registros), `PER-04-05-06.json`. El endpoint vive en `apps/reports/api/views.py` con `area = "pagos_solvencia"` y sin filtro por usuario; `familia.demo` tiene V en `pagos_solvencia`, así que pasa el permiso y recibe todo.
- **Viewport:** escritorio (API; no depende del viewport)
- **Hipótesis de causa:** el reporte se protegió por **área** (pagos_solvencia) en vez de por rol + alcance; al dar a FAM "V" en pagos_solvencia para ver su propia solvencia, heredó el reporte institucional completo. Falta `scope_queryset`-equivalente en un endpoint que no es ViewSet.

---

### A-002 · La bitácora no registra cambios de notas ni de asistencia (RNF-06)

- **Caso del plan:** `BIT-01`
- **Tipo:** falta-funcionalidad
- **Severidad:** **Alta**
- **Rol con el que ocurrió:** `docente.demo` (quien cambia) y `dir.demo` (quien consulta)
- **Dónde:** `/administrativo/bitacora` (pestaña "Cambios"); API `GET /api/v1/audit-log/?entity=grading.Grade` y `?entity=attendance.Attendance`
- **Referencia:** RNF-06 (el propio servicio de pagos cita "RNF-06: notas, pagos y asistencia"); el encabezado de la pantalla dice "Quién cambió notas, pagos, asistencia y cuentas"; el frontend mapea las entidades `grading.Grade` y `attendance.Attendance`.
- **Pasos para reproducir:**
  1. Con `docente.demo`, crear una nota válida: `POST /api/v1/grades/` `{enrollment, activity, raw_score:"8.50"}` → **201** (la nota se guarda).
  2. Con `docente.demo`, registrar asistencia: `POST /api/v1/attendance/` `{enrollment, date:"2026-10-07", status:"tarde"}` → **201**.
  3. Con `dir.demo`, consultar `GET /api/v1/audit-log/?entity=grading.Grade&page_size=1` y `?entity=attendance.Attendance&page_size=1`.
  4. Comparar con un pago: `POST /api/v1/payments/` (con `pagos.demo`) → 201 y **sí** aparece en `?entity=Payment`.
- **Esperado:** cada cambio de nota y de asistencia deja registro en la bitácora con quién, cuándo y valor anterior/nuevo (o al menos el valor nuevo al crear).
- **Obtenido:** `grading.Grade = 0` y `attendance.Attendance = 0` entradas (antes y después de los cambios); el pago sí queda (`Payment` 355 → 356). Volcado de entidades realmente auditadas: solo `Payment` (356) y `accounts.User` (25). Ningún servicio de `grading` ni `attendance` llama a `registrar_cambio` (solo `accounts/services/auth.py` y `payments/services/payment.py`).
- **Reproducible:** siempre
- **Evidencia:** `BIT.json` (`baseline`, `cambios`, `entidades`, `ultimos`), `A-002-nota-sin-auditoria.json` (POST /grades/ → 201 y bitácora `grading.Grade=0`, `attendance.Attendance=0`), `BIT-UI-cambios.png`.
- **Viewport:** escritorio
- **Hipótesis de causa:** los servicios de notas/asistencia nunca se instrumentaron con `registrar_cambio`; el mapa `ENTIDADES` del frontend quedó listo para entidades que el backend no escribe.

---

### A-003 · La emisión de documentos no queda en la bitácora de cambios

- **Caso del plan:** `BIT-03`
- **Tipo:** falta-funcionalidad
- **Severidad:** **Media**
- **Rol con el que ocurrió:** `dir.demo` (emite) / `dir.demo` (consulta)
- **Dónde:** `POST /api/v1/solvency/<enrollment>/certificate/` y `GET /api/v1/audit-log/`
- **Referencia:** BIT-03 ("Emitir un documento → queda registro de emisión"); RNF-06
- **Pasos para reproducir:**
  1. `POST /api/v1/solvency/<enrollment>/certificate/` como Dirección → **200** (el documento se crea: `GET /documents/` pasa de 0 a 1).
  2. Buscar en `/api/v1/audit-log/` cualquier entidad de documentos (`GET /audit-log/?page_size=200` × 2 páginas).
- **Esperado:** un registro de emisión (quién, cuándo, qué documento/estudiante).
- **Obtenido:** la constancia se emite y descarga, pero **no hay ninguna entidad de documentos** en la bitácora (entidades auditadas: `Payment`, `accounts.User`). El `AccessLog` sí guarda la *petición* (`/api/v1/solvency/...`) como acceso, pero no es un registro de emisión con datos del documento.
- **Reproducible:** siempre
- **Evidencia:** `BIT.json` → `bit03` (`documentosAntes: 0`, `documentosDespues: 1`, `entidadDocumentoEnBitacora: []`).
- **Viewport:** escritorio

---

### A-004 · Unidades de ciclo con fechas invertidas, traslapadas o fuera del ciclo se guardan sin validación (RN-02/HU-02)

- **Caso del plan:** `CAT-04`
- **Tipo:** datos / bug
- **Severidad:** **Alta**
- **Rol con el que ocurrió:** `dir.demo`
- **Dónde:** `POST /api/v1/cycles/<cycle>/units/` (pantalla `/administrativo/catalogo/ciclos` → "Unidades")
- **Referencia:** RN-02, HU-02 (validación de fechas de unidades)
- **Pasos para reproducir:**
  1. Crear un ciclo de prueba (`POST /cycles/`, p. ej. año 2098).
  2. Crear una unidad con fin anterior al inicio: `{number:1, start_date:"2098-05-01", end_date:"2098-04-01"}`.
  3. Crear una unidad que se traslapa con otra: `{number:2, start_date:"2098-04-01", end_date:"2098-06-01"}`.
  4. Crear una unidad fuera del rango del ciclo: `{number:3, start_date:"2097-12-01", end_date:"2098-02-01"}` con ciclo 2098-01-15 → 2098-10-30.
- **Esperado:** 400 con mensaje claro (fechas invertidas, traslape, fuera del ciclo). RN-02 fija la estructura de 4 unidades con inicio y cierre coherentes.
- **Obtenido:** **201 en los tres casos** y las fechas quedan persistidas tal cual (se verificó releyendo cada unidad: `start=2098-05-01 / end=2098-04-01`, etc.). Las 4 unidades bien formadas también se crean (201) y calculan `grades_due_date`/`report_card_enabled_date`.
- **Reproducible:** siempre
- **Evidencia:** `CAT.json` (`cat04.unidades`, `invertida:201`, `traslapada:201`, `fueraDelCiclo:201`), `CAT2.json` (`cat04confirm` con las fechas guardadas).
- **Viewport:** escritorio
- **Hipótesis de causa:** `GradingUnitSerializer` valida campos sueltos pero no la coherencia entre `start_date`/`end_date` ni contra el ciclo; la regla de RN-02 probablemente vive solo en el dominio del frontend, que no la aplica en este formulario/POST.

---

### A-005 · Pantallas completas que fallan por consultar catálogos sin permiso (Coordinación y Encargado de pagos)

- **Caso del plan:** `PER-03` (solo lectura) / `PER-01` (el menú ofrece la pantalla)
- **Tipo:** permisos / bug
- **Severidad:** **Alta**
- **Rol con el que ocurrió:** `coord.demo`, `pagos.demo`
- **Dónde:**
  - `coord.demo` → `/administrativo/asignaciones`: "No se pudo cargar la lista de asignaciones." (403 en `GET /users/?page_size=200`).
  - `coord.demo` → `/administrativo/horarios`: "No se pudo cargar el horario." (403 en `GET /users/?page_size=200`).
  - `pagos.demo` → `/administrativo/estudiantes`: "No se pudo cargar la lista de estudiantes." (403 en `GET /sections/` y `GET /scholarships/`).
  - `pagos.demo` → `/administrativo/documentos`: "No se pudo cargar la bandeja de documentos." (403 en `GET /document-types/`).
- **Referencia:** `docs/permisos-roles.md` (COORD tiene **V** en `horarios_calendario`; PAGOS tiene **E** en `documentos` y **V** en `estudiantes_encargados`); el menú les muestra esas pantallas (PER-01).
- **Pasos para reproducir:** entrar con el rol y abrir la URL indicada; los 403 exactos salen en Network.
- **Esperado:** la pantalla carga en modo lectura (esos roles sí tienen acceso al área), resolviendo nombres con un recurso permitido o degradando sin romper.
- **Obtenido:** la página entera se reemplaza por el `ErrorBanner` con "Reintentar"; la funcionalidad es inutilizable para esos roles aunque la matriz les da acceso. Otras pantallas de los mismos roles cargan bien (p. ej. coord `/administrativo/estudiantes`, `/administrativo/calendario`; pagos `/administrativo/pagos`).
- **Reproducible:** siempre
- **Evidencia:** `A-005-barrido-403.json` (alerta y 403 por rol y pantalla), `PER-03-coord-asignaciones.png`, `PER-03-coord-horarios-red.png`, `PER-03-admin-pagos.png`.
- **Viewport:** escritorio
- **Hipótesis de causa:** las páginas piden *lookups* auxiliares por endpoints de otras áreas (`/users/` es `usuarios_roles`; `/sections/`, `/scholarships/`, `/document-types/` son `datos_maestros`) y tratan cualquier 403 como error fatal de la pantalla, en vez de deshabilitar el cruce o pedir solo lo permitido. Se ve tanto en Coordinación como en Pagos, así que es sistemático, no un caso aislado.

---

### A-006 · Los catálogos permiten nombres duplicados

- **Caso del plan:** `CAT-03`
- **Tipo:** datos / falta-funcionalidad
- **Severidad:** **Media**
- **Rol con el que ocurrió:** `dir.demo`
- **Dónde:** `POST /api/v1/courses/` (aplica a los catálogos simples)
- **Referencia:** CAT-03 ("duplicados… validación clara")
- **Pasos para reproducir:**
  1. `POST /api/v1/courses/` `{name:"Matemática", type:"academico"}` (ya existe "Matemática" de la siembra) → **201**; quedan dos cursos con el mismo nombre.
- **Esperado:** 400 con mensaje de duplicado (o una regla explícita si se permiten).
- **Obtenido:** 201; el duplicado entra y aparece en los selectores (dos "Matemática"). Vacíos (400), nombre de 300 caracteres (400) y caracteres especiales/ñ (201, sin 500) se comportaron bien.
- **Reproducible:** siempre
- **Evidencia:** `CAT.json` (`cat03.duplicadoCurso:201`), limpieza en `CAT2.json`.
- **Viewport:** escritorio

---

### A-007 · Rutas inexistentes: pantalla en blanco en vez de un 404 amable

- **Caso del plan:** `ACC-13`
- **Tipo:** ux
- **Severidad:** **Media**
- **Rol con el que ocurrió:** cualquier rol con sesión
- **Dónde:** p. ej. `/loquesea` y `/administrativo/zzz`
- **Referencia:** ACC-13 ("página 404 amable, no pantalla en blanco")
- **Pasos para reproducir:** con sesión activa, escribir una URL no definida.
- **Esperado:** página 404 con enlace de vuelta.
- **Obtenido:** `<body>` vacío, la URL no redirige y no hay `h1`; pantalla totalmente en blanco.
- **Reproducible:** siempre
- **Evidencia:** `ACC-06-08-09-12-13.json`, `ACC-13--loquesea-con-sesion.png`, `ACC-13--administrativo-zzz-con-sesion.png`. Nota: **sin sesión**, `/loquesea` sí redirige a `/ingresar` (eso funciona); el fallo es solo con sesión activa.
- **Viewport:** escritorio

---

### A-008 · Selectores de otras pantallas ofrecen registros dados de baja

- **Caso del plan:** `CAT-02`
- **Tipo:** ux / datos
- **Severidad:** **Media**
- **Rol con el que ocurrió:** `dir.demo`
- **Dónde:** filtro "Sección" de `/administrativo/reportes` y de `/administrativo/asistencia` (mismo patrón en cualquier selector que liste secciones)
- **Referencia:** CAT-02 ("se desactiva… **no** en selectores nuevos")
- **Pasos para reproducir:**
  1. Abrir `/administrativo/reportes` y desplegar el filtro "Sección".
  2. Ver que aparecen "Taller de panadería" (dada de baja en la siembra) y las secciones QA dadas de baja.
- **Esperado:** los selectores ofrecen solo registros activos.
- **Obtenido:** aparecen inactivas: `["QA Segundo Y", "QA Taller", "Taller de panadería"]`. La API de listas devuelve también inactivos y ese selector no filtra `is_active`. (La baja lógica en sí funciona bien: el registro sigue existiendo con `is_active=false` y los históricos lo conservan.)
- **Reproducible:** siempre
- **Evidencia:** `PER03-PER01-TRV.json` → `selectores`, `TRV-selector-secciones.png`, `CAT-05-selector-seccion-asistencia.png`, `CIERRE-HUECOS.json`.
- **Viewport:** escritorio

---

### A-009 · Se puede "cambiar" la contraseña por la misma contraseña

- **Caso del plan:** `ACC-11`
- **Tipo:** mejora / seguridad (endurecimiento)
- **Severidad:** **Mejora**
- **Rol con el que ocurrió:** usuario de prueba `qa.ui.tildes`
- **Dónde:** `POST /api/v1/auth/change-password/` (pantalla `/operativo/cuenta`)
- **Referencia:** no documentado (ACC-11 pide "reutilizar la misma" como caso a probar)
- **Pasos para reproducir:** con una sesión válida, enviar `contrasena_actual` = `contrasena_nueva` (misma cadena).
- **Esperado:** rechazar la reutilización con un mensaje ("elegí una contraseña distinta").
- **Obtenido:** 204, se acepta. El resto de reglas de ACC-11 sí funcionan: contraseña actual incorrecta ("La contraseña actual no es correcta."), nueva corta (error genérico del validador), confirmación distinta bloquea el botón con "No coincide con la contraseña nueva.", y tras cambiar entra la nueva y no la vieja.
- **Reproducible:** siempre
- **Evidencia:** `USR-ACC02-ACC11-UI.json` (`acc11`), salida de `/tmp/opencode/qa/reuse.cjs` (204).
- **Viewport:** escritorio

---

### A-010 · El registro de accesos guarda rutas técnicas de API, no pantallas legibles

- **Caso del plan:** `BIT-02`
- **Tipo:** ux / mejora
- **Severidad:** **Mejora**
- **Rol con el que ocurrió:** `dir.demo` (consulta), `familia.demo` (genera)
- **Dónde:** `/administrativo/bitacora` → pestaña "Accesos"; API `GET /api/v1/access-log/`
- **Referencia:** RNF-07; BIT-02 ("queda registro de acceso")
- **Pasos para reproducir:** iniciar sesión con `familia.demo`, navegar por el portal y ver los accesos en la bitácora.
- **Esperado:** quién y qué pantalla consultó, en lenguaje entendible para Dirección.
- **Obtenido:** el registro existe y es correcto (usuario, fecha, y filtra por persona; 83 registros de la familia), pero `screen_viewed` guarda **rutas técnicas**: `/api/v1/auth/me/`, `/api/v1/students/`, `/api/v1/calendar/weekly/`, `/api/v1/reports/insolvent-students/`… La columna "Qué consultó" muestra esas rutas crudas. Sugerencia: mapear a nombres de pantalla ("Notas", "Calendario").
- **Reproducible:** siempre
- **Evidencia:** `BIT.json` (`bit02`), `BIT-UI-accesos.png`.
- **Viewport:** escritorio

---

### A-011 · Entrar por `127.0.0.1:5173` no permite iniciar sesión (documentado, pero se confirma)

- **Caso del plan:** `ACC-10`
- **Tipo:** ux / ops
- **Severidad:** **Baja**
- **Rol con el que ocurrió:** cualquiera
- **Dónde:** `http://127.0.0.1:5173` (en lugar de `localhost:5173`)
- **Referencia:** el LEEME pide documentarlo; cookie `SameSite=Strict` + `CORS_ALLOWED_ORIGINS=http://localhost:5173`
- **Pasos para reproducir:** abrir el portal por `127.0.0.1` e intentar ingresar.
- **Esperado:** documentar el comportamiento.
- **Obtenido:** el login no completa: las llamadas a `/auth/refresh/` y `/auth/login/` quedan bloqueadas por CORS (sin `Access-Control-Allow-Origin` para el origen `http://127.0.0.1:5173`) y no se puede entrar. Con `localhost` funciona perfecto. No es un defecto del sistema, pero conviene que esté en la guía de demo para no pisarlo.
- **Reproducible:** siempre
- **Evidencia:** `ACC-10-127001.png`, `ACC-06-10-12-13.json`.
- **Viewport:** escritorio

---

## Apéndice — Diagnóstico de K-1 (hallazgo conocido, no se reporta como nuevo)

**K-1: "la sesión no persiste entre recargas".** No reproduce en el flujo normal y la cookie está bien:

- **ACC-04/ACC-05 ✅:** tras cerrar la pestaña y tras cerrar el navegador completo, con perfil persistente, la cookie `refresh_token` existe con `Max-Age=604800` (+7 días), `HttpOnly`, `SameSite=Strict`, `Path=/api/v1/auth/`, dominio `localhost`, `Secure=false` en local; `POST /auth/refresh/` → 200; la sesión sigue.

- **Causa raíz aislada (carrera con la rotación del refresh):** con **F5 separados 2.5 s** → `/auth/refresh/` responde `[200,200,200]` y la sesión queda estable. Con **recargas rápidas consecutivas (6 sin espera)** → `[401,401,401,401,401]`, sin `Set-Cookie` en las fallidas, y cae a `/ingresar`. El backend usa `ROTATE_REFRESH_TOKENS=True` + `BLACKLIST_AFTER_ROTATION=True`: al recargar en ráfaga, una petición rota y blacklistea el token viejo, pero la cookie nueva no llega a guardarse (peticiones abortadas/superpuestas) y el siguiente refresh usa el token ya blacklisteado → 401 → logout.
- **Evidencia:** `ACC-04-05.json`, `K1-race.json`, `ACC-04-reabrir-pestana.png`, `ACC-05-reabrir-navegador.png`. Sugerencia: serializar el refresh en el cliente (ya hay `refrescoEnCurso` en `app/http.ts`) **y** no rotar/blacklistear tan agresivamente en desarrollo, o reintentar `refresh` una vez con la cookie previa.

---

## Cobertura de mi set

Marca cada caso: ✅ pasó · ❌ falló (ver hallazgo) · ⏭️ no se pudo probar (por qué)

| Caso | Estado | Hallazgo(s) |
|---|---|---|
| ACC-01 Login 8 roles | ✅ | |
| ACC-02 Mensajes de error de login | ✅ | usuario inexistente y contraseña mala dan el **mismo** mensaje; campos vacíos no envían |
| ACC-03 11 intentos → 429 | ✅ | 10×401 y luego 429; mensaje "Demasiados intentos…"; recupera al minuto |
| ACC-04 Cerrar pestaña y volver | ✅ | K-1 no reproduce (ver apéndice) |
| ACC-05 Cerrar navegador completo | ✅ | K-1 no reproduce (ver apéndice) |
| ACC-06 F5 y enlaces directos | ✅ | 3 portales |
| ACC-07 >15 min y seguir usando | ✅ | refresh silencioso 200, sigue logueado. La segunda mitad ("no pierde lo escrito") se deriva del diseño SPA: el refresh no recarga la página; no se simuló un formulario a medias durante 15 min |
| ACC-08 Logout + botón Atrás | ✅ | termina en `/ingresar`, sin contenido protegido |
| ACC-09 Logout con otra pestaña | ✅ | la otra pestaña pide login al siguiente request |
| ACC-10 Entrar por 127.0.0.1 | ❌ | A-011 (documentado; CORS bloquea) |
| ACC-11 Cambio de contraseña (reglas) | ✅ | A-009 (reutilización permitida, Mejora) |
| ACC-12 `/ingresar` con sesión | ✅ | redirige al portal |
| ACC-13 Rutas inexistentes | ❌ | A-007 (con sesión, pantalla en blanco). Sin sesión redirige a `/ingresar` (correcto) |
| PER-01 Menú por rol | ✅ | notas en "Cosas raras" (COORD/DOC/GUÍA/TALL) |
| PER-02 URLs prohibidas | ✅ | tras repetir tallerista con login fresco |
| PER-03 Solo lectura | ❌ | A-005 (coord/pagos) y A-001 (alcance API) |
| PER-04 RBAC API (token/rol) | ❌ | A-001 (fuga con token de familia) |
| PER-05 Alcance por objeto | ✅ | secciones ajenas 403 |
| PER-06 Datos sensibles | ✅ | dir E, admin V, resto 403 |
| PER-07 Usuario desactivado con sesión | ✅ | token pasa a 401 en el siguiente request |
| USR-01 Crear por rol + temporal obligatoria | ✅ | 7 roles; credenciales una sola vez; fuerza cambio |
| USR-02 Validaciones | ✅ | duplicado 400, correo 400, vacíos bloquean, ñ/tildes 201 |
| USR-03 Editar rol y menú | ✅ | Docente→Tallerista; al reingresar muestra el menú de tallerista (`USR-03-menu-tras-cambio-rol.png`) |
| USR-04 Desactivar/reactivar | ✅ | desactivado no entra; datos se conservan |
| USR-05 Restablecer contraseña | ✅ | temporal + obliga cambio |
| USR-06 Quién accede a Usuarios | ✅ | solo Dirección/Admin (API 403 al resto) |
| USR-07 Quitarse rol/desactivarse | ✅ | 400 "No podés desactivar tu propia cuenta." / "No podés cambiar tu propio rol."; la UI ni muestra el botón en tu fila |
| BIT-01 Cambios en notas/pagos/asistencia | ❌ | A-002 (notas y asistencia no se auditan) |
| BIT-02 Login de familia y consultas | ✅ | A-010 (rutas técnicas, Mejora) |
| BIT-03 Emitir documento | ❌ | A-003 |
| BIT-04 Filtros/paginación/orden/rendimiento | ✅ | 381 registros, 25/pág, orden desc, filtro por entidad, 200 en ~42 ms |
| CAT-01 Recorrer 8 catálogos | ✅ | crear/editar 201/200; Coordinación solo ve (403 al crear) |
| CAT-02 Desactivar en uso / sin uso | ✅ | soft-delete correcto; **A-008** por selectores que aún las ofrecen |
| CAT-03 Duplicados/vacíos/largos/especiales | ❌ | A-006 (duplicado 201); el resto ok, sin 500 |
| CAT-04 Ciclo: 4 unidades y fechas | ❌ | A-004 |
| CAT-05 Secciones académica/taller | ✅ | taller 201; académica con guía correcto 201; sin el rol correcto 400 con mensaje claro; la sección nueva aparece en el selector de Asistencia |
| CAT-06 Selectores reflejan catálogo nuevo | ✅ | el curso recién creado aparece en el selector de Asignaciones (`CAT-06-selector-curso.png`) |
| REP-01 Los 8 reportes | ✅ | todos 200; filtros ciclo/sección/unidad acotan (480→80, 60→10, 22→3…) |
| REP-02 PDF de cada uno | ✅ | 8 PDFs; coinciden con pantalla (80 registros, "Daniela Batz Tzul"); sin firma digital |
| REP-03 Filtros sin resultados | ✅ | "Sin resultados / No hay registros para los filtros elegidos." y PDF "0 registros" |
| REP-04 Métricas | ✅ | 2 porcentajes sin datos personales (procesos 83 %, portal de familias 3 %) |
| REP-05 Quién accede | ✅ | DIR/COORD/ADMIN 200; PAGOS solo insolventes (nota 8); resto 403 |
| QR-01 Verificar sin sesión | ✅ | tipo, estudiante y fecha; sin datos sensibles |
| QR-02 Código inválido | ✅ | "Este código no corresponde a un documento válido." |
| QR-03 Con sesión de otro rol | ✅ | misma vista (texto idéntico) |
| TRV-01 Móvil 375 px | ✅ | Bitácora sin desborde horizontal (`TRV-movil-bitacora-375.png`) |
| TRV-02 Estados cargando/vacío/error | ✅ | backend cortado en vivo a media pantalla: banner "No se pudo cargar…" + "Reintentar" (no pantalla en blanco) y recupera al reintentar (`TRV-02-error-de-red.png`, `TRV-02-recuperado.png`) |
| TRV-03 Formularios | ✅ | required, correo, confirmación; mensajes claros |
| TRV-04 Doble envío | ✅ | doble clic en "Crear usuario" → 1 sola cuenta (`TRV-doble-envio.png`) |
| TRV-05 Refresco de listas | ✅ | tras crear/editar/desactivar, la lista se recarga |
| TRV-06 Navegación/F5/enlaces | ✅ | ACC-06/12 |
| TRV-07 Textos | ✅ | revisados; ver A-010 (nombres técnicos) |
| TRV-08 Fechas/números | ✅ | es-GT consistente en pantallas y PDFs (no se pudo probar el borde de medianoche) |
| TRV-09 Consola | ✅ | sin errores en el barrido (aparte de 401/403 esperados) |
| TRV-10 Red sin 500 | ✅ | ningún 5xx en el barrido de Set A |
| TRV-11 Teclado | ✅ | Tab lleva a usuario→contraseña y Enter envía |
| TRV-12 PDF sin firma digital | ✅ | ningún PDF menciona firma; RN-15 respetada |
| TRV-13 Identidad visual | ✅ | capturas por pantalla en `QA-setA-evidencias/` |

---

## Cosas que me parecieron raras pero no estoy seguro de que sean error

- **Coordinación ve "Avisos" y "Reportes de conducta"** y la matriz los tenía como "¿?" en el documento de permisos: hoy están implementados como **V**. Puede ser intencional; conviene alinear la matriz.
- **DOC/GUÍA/TALL tienen V en `estudiantes_encargados`** en la matriz, pero el portal operativo **no tiene pantalla de Estudiantes**; ese V acotado no se ejerce en ninguna vista.
- El **reporte de insolventes** aparece en "Reportes institucionales" **y** como botón en "Pagos y solvencia"; el plan dice que vive en Pagos. Duplicación funcional (y la causa de A-001: el área con la que se protegió es `pagos_solvencia`).
- Las **listas de la API incluyen registros dados de baja** (`/cycles/`, `/sections/`); el frontend los filtra en unos selectores (Asignaciones filtra cursos inactivos) pero no en otros (Reportes, Asistencia → A-008). Puede ser por diseño (históricos) y a la vez origen de selectores sucios.
- El **orden de roles** en "Crear usuario" es alfabético y arranca en "Administrador del sistema"; el primero de la lista no es "Docente" como uno esperaría. Cosmético.
- En **`/reports/schedules/`** el filtro por `section` necesita el `public_id` de la sección y funciona; en cambio `GET /assignments/?section=<id>` **ignora** el filtro y devuelve todas (49). No lo usa la UI, pero puede confundir a quien consuma la API.
- Los **reportes no paginan** (devuelven todas las filas, sin `count`); para los volúmenes actuales va bien (480 filas), pero "Accesos de las familias" crecerá sin techo.
