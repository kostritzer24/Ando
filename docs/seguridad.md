# Revisión de seguridad — OWASP Top 10 (2021)

Sección 14.4 del prompt maestro exige esta revisión con evidencia de cómo se
atiende cada categoría. Se documenta lo ya implementado en fases anteriores
y lo agregado en la Fase 13 (Endurecimiento) para cerrar los huecos que esta
revisión encontró. Igual que el resto de la documentación del proyecto, lo
que no se pudo verificar en el código queda marcado como tal, no se asume.

## A01:2021 — Pérdida de control de acceso

- Deniega por defecto: `DEFAULT_PERMISSION_CLASSES` es `apps.core.permissions.DenyAll`
  (`backend/config/settings/base.py`) — ningún endpoint queda abierto por
  omisión. Cada vista concede explícitamente con `PermisoPorArea`
  (`backend/apps/core/permissions.py`), que compara el rol del usuario
  contra el área que la vista declara (`docs/permisos-roles.md`).
- Alcance a nivel de objeto separado del permiso a nivel de rol:
  `ScopedQuerysetMixin` (`backend/apps/core/api/mixins.py`) obliga a que
  todo listado/detalle filtre el queryset a partir del usuario autenticado,
  nunca comparando un id de la URL contra el usuario — evita el error
  clásico de IDOR ("cambiar un número en la barra de direcciones expone
  el expediente de otro menor", según el comentario del propio código).
- Los identificadores que ve el cliente son `public_id` (UUID), nunca el
  `id` interno autoincremental — un UUID no se puede enumerar ni adivinar
  secuencialmente como sí se podría con un entero correlativo.
- Los documentos emitidos (constancias, boletines) no se sirven desde una
  carpeta pública de `MEDIA_ROOT`: se descargan por una vista autenticada
  que lee el archivo del disco (`SECURE_CONTENT_TYPE_NOSNIFF`, comentario
  en `backend/config/settings/base.py`).

## A02:2021 — Fallas criptográficas

- `SECRET_KEY` viene de variable de entorno, nunca hardcodeada
  (`backend/config/settings/base.py`).
- Contraseñas con el hasher por defecto de Django (PBKDF2), nunca en texto
  plano ni con hash propio.
- En producción (`backend/config/settings/production.py`): `SECURE_SSL_REDIRECT`,
  HSTS con subdominios, `SESSION_COOKIE_SECURE`/`CSRF_COOKIE_SECURE` — HTTPS
  obligatorio de punta a punta.
- La cookie del token de refresco (`REFRESH_COOKIE_*`,
  `backend/config/settings/base.py`) es `Secure`, `HttpOnly` (fijada así en
  `_set_refresh_cookie`, `backend/apps/accounts/api/views.py`) y
  `SameSite=Strict`, con alcance restringido a `/api/v1/auth/` — nunca
  viaja fuera de ese path ni de una conexión cifrada.
- El token de acceso (15 min) vive solo en memoria del frontend, nunca en
  `localStorage` ni en una cookie — no queda expuesto a un XSS que lea
  almacenamiento persistente.

## A03:2021 — Inyección

- Toda consulta usa el ORM de Django con parámetros ligados; no hay una
  sola llamada a `.raw()`, `.extra()` ni `cursor()` en todo `apps/`
  (verificado con una búsqueda en el código fuente para esta revisión) —
  sin superficie de inyección SQL.
- Las plantillas Excel de asistencia/notas se leen con
  `load_workbook(archivo, data_only=True, read_only=True)`
  (`backend/apps/attendance/services/template.py`,
  `backend/apps/grading/services/template.py`) y se rechaza explícitamente
  `.xlsm` — no se evalúa ninguna fórmula ni macro del archivo que sube el
  usuario, conforme a la sección 14.4 ("no se ejecuta nada de lo que
  traigan, incluidas fórmulas y macros").
- Los PDF (boletín, constancias, reportes) se arman con
  `django.template.loader.render_to_string` + WeasyPrint: la interpolación
  pasa por el autoescape de plantillas de Django, no por concatenación de
  strings.

## A04:2021 — Diseño inseguro

- RN-16 (`backend/apps/communication/domain/buzon.py`): el Buzón filtra
  lenguaje inapropiado por coincidencia de palabra completa antes de crear
  el mensaje, y bloquea temporalmente a quien lo envió — la validación de
  contenido es parte del diseño del flujo, no un parche posterior.
- RN-12: la resolución de una justificación de falta siempre la evalúa una
  persona (Dirección); nunca se aprueba automáticamente por la sola
  presencia de un documento adjunto.
- Límite de tasa por endpoint sensible ya en el diseño del throttling
  (`DEFAULT_THROTTLE_RATES`, `backend/config/settings/base.py`): `login`
  (10/min) y `verificacion_qr` (30/min) tienen su propio scope, más
  restrictivo que el límite general de usuario autenticado (120/min) o
  anónimo (20/min) — pensado para frenar fuerza bruta contra login y
  contra el código de verificación de documentos emitidos.
- Datos sensibles (salud, socioeconómicos) van en un serializer y un
  endpoint separado del expediente general
  (`GET /students/{id}/sensitive/`, `docs/api.md`), no como campos más
  de la respuesta estándar — quien solo tiene `ver` en Estudiantes nunca
  recibe esos campos ni por accidente de serialización.

## A05:2021 — Configuración incorrecta de seguridad

- `DEBUG = False` fijado en `base.py`, y los tres entornos heredan de ahí
  sin volver a activarlo salvo en `config/settings/local.py`
  (desarrollo local, nunca se despliega).
- `X_FRAME_OPTIONS = "DENY"` y `SECURE_CONTENT_TYPE_NOSNIFF = True`
  (`backend/config/settings/base.py`) — protección contra clickjacking y
  contra MIME-sniffing.
- **Agregado en esta fase:** `Content-Security-Policy` — el `MIDDLEWARE`
  no traía ninguna hasta ahora. Se agregó
  `PoliticaDeSeguridadDeContenidoMiddleware`
  (`backend/apps/core/middleware.py`) con una política de "mismo origen
  por defecto" (`default-src 'self'`, `frame-ancestors 'none'`,
  `form-action 'self'`), sin agregar una dependencia nueva (regla de
  trabajo 8) porque la API solo sirve JSON, PDF y la interfaz explorable
  de DRF.
- `CORS_ALLOWED_ORIGINS` se arma desde variable de entorno, nunca con
  comodín (`*`), y `CORS_ALLOW_CREDENTIALS = True` solo tiene efecto junto
  a un origen explícito — Django/`django-cors-headers` rechaza combinar
  credenciales con comodín.
- **Protección contra CSRF, ya cubierta sin `CsrfViewMiddleware`:** los
  únicos dos endpoints que consumen la cookie de sesión
  (`/auth/refresh/`, `/auth/logout/`) usan una cookie `SameSite=Strict` —
  el navegador nunca la adjunta en una petición disparada desde otro
  origen, así que el ataque que el token CSRF de Django previene (una
  petición de otro sitio que arrastra la cookie) ya no tiene vector: la
  cookie simplemente no viaja. El resto de la API no usa cookies para
  autenticar (usa el header `Authorization: Bearer`), que tampoco es
  vulnerable a CSRF porque un sitio ajeno no puede leer ni fijar ese
  header. Por eso `CsrfViewMiddleware` está deliberadamente ausente de
  `MIDDLEWARE`, no es un olvido.
- `ALLOWED_HOSTS` explícito por entorno, nunca `["*"]`.

## A06:2021 — Componentes vulnerables o desactualizados

Revisión de dependencias hecha en esta fase (`backend/requirements/*.txt`),
con investigación puntual de CVEs conocidos en vez de asumir que "más
nuevo es más seguro":

- **`djangorestframework-simplejwt` 5.3.1 → 5.5.1**: corrige CVE-2024-22513
  (un usuario inactivo o dado de baja podía seguir autenticándose vía
  refresco de token). Confirmado con la lista de versiones de PyPI y el
  aviso de la vulnerabilidad.
- **Django 5.1.2 → 5.2.17 (LTS)**: la rama 5.1 llegó a fin de soporte de
  seguridad el 2025-12-31; 5.2 es la rama LTS vigente. Se prefirió sobre
  saltar a Django 6.x para no sumar riesgo de regresión en una fase de
  endurecimiento.
- `drf-spectacular`, `django-cors-headers`, `psycopg`, `factory-boy` y
  `ruff` actualizados a su última versión estable sin CVE pendiente
  conocido.
- `weasyprint` ya estaba en la versión donde el aviso de CVE-2026-55073
  indica textualmente que el problema "está corregido en la versión 70.0"
  — sin acción pendiente.
- `gunicorn` y `pytest` se dejaron sin subir de versión mayor: no se
  encontró un CVE que lo justificara y el salto es más grande de lo que
  amerita una pasada de endurecimiento (`pytest` 9.x cambia
  comportamiento de fixtures).
- Todo el cambio se verificó en vivo: `manage.py check` limpio,
  `makemigrations --check --dry-run` sin cambios de esquema, y el suite
  completo de pruebas del backend en verde antes y después del cambio.

## A07:2021 — Fallas de identificación y autenticación

- JWT de dos piezas (sección 14.1): token de acceso de 15 minutos en
  memoria, token de refresco de 7 días con rotación y lista negra tras
  cada rotación (`ROTATE_REFRESH_TOKENS`, `BLACKLIST_AFTER_ROTATION`,
  `backend/config/settings/base.py`) — un refresco robado deja de servir
  en cuanto se usa una vez más por el usuario legítimo.
- Política de contraseña: longitud mínima 10, más los validadores
  estándar de Django (`CommonPasswordValidator`, `NumericPasswordValidator`)
  y uno propio, `ContrasenaComunEsValidator`
  (`backend/apps/core/validators.py`), que rechaza contraseñas comunes en
  español además de la lista en inglés que ya trae Django.
- `throttle_scope = "login"` (`backend/apps/accounts/api/views.py`) limita
  los intentos de inicio de sesión a 10 por minuto — frena fuerza bruta de
  contraseña.
- `UPDATE_LAST_LOGIN = True` deja rastro de cada inicio de sesión exitoso.

## A08:2021 — Fallas de integridad de software y datos

- Los documentos emitidos llevan código de verificación
  (`verification_code`) y una vista pública de verificación con su propio
  límite de tasa (`throttle_scope = "verificacion_qr"`, 30/min) — evita
  que alguien fuerce por fuerza bruta códigos de verificación válidos.
- **Agregado en esta fase:** validación de todo archivo que sube un
  usuario, por tipo declarado, tipo real (firma binaria) y tamaño
  (`validar_documento_de_respaldo`, `backend/apps/core/validators.py`),
  conectada al único campo de subida de archivo genuina de un usuario en
  todo el sistema: `Justification.supporting_document` (RF-12). El otro
  `FileField` del proyecto, `IssuedDocument.file`, lo genera el propio
  servidor con WeasyPrint y nunca lo sube una persona, así que no
  necesitaba esta validación.
- `git` es la fuente de verdad de todo despliegue; no hay actualización
  automática de dependencias sin revisión (`requirements/*.txt` fija
  versión exacta con `==`, no un rango).

## A09:2021 — Fallas de registro y monitoreo de seguridad

- `AuditLog` (`backend/apps/core/models.py`) registra cada cambio sensible
  con usuario, fecha y el detalle del cambio (ADR-0004: registra cambios,
  no lecturas).
- `AccessLog` (`backend/apps/core/models.py`) registra qué pantalla
  consultó cada usuario — cubre el caso de consultas a datos sensibles
  que `AuditLog` no alcanza por diseño (nota 9,
  `docs/permisos-roles.md`): toda consulta de un dato sensible por
  ejemplo, `GET /students/{id}/sensitive/`) queda con usuario, fecha y
  pantalla, aunque sea solo lectura.
- Ningún dato personal viaja en registros técnicos, mensajes de error que
  llegan al navegador, ni en la URL (sección 14.3 del prompt maestro).

## A10:2021 — Falsificación de solicitud del lado del servidor (SSRF)

- El backend no hace ninguna petición saliente a una URL que dependa de
  una entrada del usuario: no hay un solo `import requests`, `urllib.request`
  ni `httpx` en todo `apps/` (verificado con una búsqueda en el código
  fuente para esta revisión) — no hay superficie de SSRF porque no hay
  ninguna llamada de red saliente que el proyecto controle.
- El único contenido externo que el sistema genera son los PDF (WeasyPrint
  renderiza HTML propio, no una URL arbitraria) y el QR de verificación
  (codifica un enlace propio construido desde `FRONTEND_URL`, no una URL
  que el usuario proponga).

## Resumen

| Categoría | Estado |
|---|---|
| A01 Control de acceso | Cubierto desde fases anteriores |
| A02 Criptografía | Cubierto desde fases anteriores |
| A03 Inyección | Cubierto desde fases anteriores |
| A04 Diseño inseguro | Cubierto desde fases anteriores |
| A05 Configuración | Cubierto desde fases anteriores + CSP agregado en Fase 13 |
| A06 Componentes desactualizados | Corregido en Fase 13 (simplejwt, Django) |
| A07 Autenticación | Cubierto desde fases anteriores |
| A08 Integridad de software/datos | Cubierto desde fases anteriores + validación de archivos agregada en Fase 13 |
| A09 Registro y monitoreo | Cubierto desde fases anteriores |
| A10 SSRF | No aplica — sin superficie |
