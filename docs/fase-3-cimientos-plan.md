# Fase 3 — Cimientos: plan

Plan de la fase antes de escribir código de producción, conforme a la regla de trabajo 1. Cubre RF-01 y RNF-03 a RNF-07 (sección 18 del prompt maestro). Al cerrar esta fase el sistema no hace nada del negocio todavía, pero ya es seguro y ya mide.

**Bloqueante real antes de programar:** [ADR-0007](adr/0007-bibliotecas-fundacionales.md) (JWT, esquema OpenAPI, CORS) está **propuesto, no aceptado**. No se instala nada de esa lista hasta que se confirme, igual que se hizo con ADR-0005 en la Fase 1.

## 1. Estructura de repositorio a crear

```
backend/
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── local.py
│   │   ├── test.py
│   │   └── production.py
│   ├── urls.py
│   └── wsgi.py / asgi.py
├── apps/
│   ├── accounts/        # Usuario, Rol — con capas api/services/domain/selectors
│   ├── core/             # AuditLog, AccessLog, permisos base, middleware CSP
│   ├── catalog/           # esqueleto vacío, entidades llegan en Fase 4
│   ├── students/           # esqueleto vacío, entidades llegan en Fase 5
│   ├── scheduling/          # esqueleto vacío
│   ├── attendance/           # esqueleto vacío
│   ├── grading/                # esqueleto vacío
│   ├── payments/                 # esqueleto vacío
│   ├── documents/                  # esqueleto vacío
│   ├── communication/                # esqueleto vacío
│   └── reports/                       # esqueleto vacío
├── manage.py
├── requirements/{base,local,production}.txt
└── pytest.ini

frontend/
├── src/
│   ├── app/           # main.ts, router, guards por rol, interceptor de Axios (refresh)
│   ├── pages/{administrativo,operativo,publico}/   # shells vacíos
│   ├── features/auth/  # login, cambio de contraseña obligatorio, selector de estudiante (esqueleto)
│   ├── shared/         # biblioteca de componentes base (sección 3)
│   └── design/         # tokens.css con la Propuesta B
├── e2e/                # Playwright, vacío por ahora
├── index.html, vite.config.ts, tsconfig.json
└── package.json

.github/workflows/ci.yml
.env.example
```

Solo `accounts` y `core` llevan modelos reales en esta fase. Las demás apps se crean vacías (con su `api/services/domain/selectors/models.py/tests/` en blanco) para que la estructura de capas exista desde el principio y cada fase futura solo agregue archivos, no cree carpetas nuevas a medio camino.

## 2. Configuración por entornos

Tres archivos de settings (`local`, `test`, `production`) que heredan de `base`, tal como pide la sección 17. Todo secreto sale de variables de entorno (`django-environ` no está en el stack fijado ni en los ADR — se usa `os.environ` directo con un pequeño helper en `config/settings/base.py`, para no sumar una dependencia por algo que la biblioteca estándar resuelve, regla de trabajo 8). `.env.example` documenta cada variable: `SECRET_KEY`, `DATABASE_URL` (Neon, `sslmode=require`), `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `JWT_*`, `DEBUG`.

## 3. Biblioteca de componentes base (Propuesta B — "Trámite claro")

`frontend/src/design/tokens.css` con las variables de `docs/diseno/direccion-visual.md` (Propuesta B): color, tipografía (Archivo + Public Sans vía Google Fonts), escala tipográfica, escala de espaciado, radios.

Componentes base en `frontend/src/shared/components/`, todos derivados de lo que ya aparece en la maqueta de la Fase 2 y de los principios de la sección 15.2 (una pantalla, una tarea; error útil; área táctil mínima de 44px):

| Componente | Uso |
|---|---|
| `AppButton` | Botón primario/secundario, nunca con flecha al final del texto |
| `TagPill` | Etiqueta de estado (como "Taller", "Ahora" en la maqueta) — variantes semánticas, no decorativas |
| `ListRow` | Fila con línea inferior, reemplaza la tarjeta en toda la interfaz |
| `DayTabs` | Selector de día por pestañas subrayadas |
| `TopAppBar` | Encabezado con marca, estudiante seleccionado y botón "Cambiar estudiante" |
| `BottomTabBar` | Navegación inferior del portal público |
| `EmptyState` | Estado vacío que invita a la acción siguiente (sección 15.2) |
| `ErrorBanner` | Mensaje de error con qué pasó y qué hacer, sin disculpas |
| `FormField` | Una pregunta por pantalla cuando aplica, etiqueta real, foco visible |

Cada componente lleva su prueba con Vitest (`shared/components/__tests__/`) desde que se crea, conforme a la regla de trabajo 9.

## 4. Integración continua

`.github/workflows/ci.yml` con dos jobs paralelos:

- **backend:** `ruff check`, `ruff format --check`, `pytest` con cobertura (falla si `domain/`+`services/` bajan de 80 %, sección 16).
- **frontend:** `eslint`, `vue-tsc --noEmit`, `vitest run`, `vite build`.

Corre en cada pull request, tal como pide la sección 17. Playwright no corre todavía en CI (los seis flujos de extremo a punta necesitan varias fases más de funcionalidad); se agrega su job cuando exista el primer flujo real que probar.

## 5. Autenticación (RNF-03, RNF-05, RN-14)

- `POST /auth/login/`, `POST /auth/refresh/`, `POST /auth/logout/`, `POST /auth/change-password/` (contrato ya fijado en `docs/api.md`).
- Token de acceso de 15 minutos; token de refresco rotativo en cookie `HttpOnly/Secure/SameSite=Strict`, con lista de revocación (`djangorestframework-simplejwt`, pendiente de ADR-0007).
- `User.must_change_password` fuerza el cambio en el primer ingreso (contraseña temporal generada por administración, nunca por la persona misma — RN-14, sin registro libre).
- `User.failed_login_attempts` + `User.locked_until`: bloqueo temporal creciente por usuario y limitador adicional por IP vía throttling de DRF.
- Validadores de contraseña de Django + una lista corta de contraseñas comunes en español como validador adicional (archivo de datos en `core/`, no una biblioteca).

## 6. Roles y permisos (RNF-03, RNF-04)

- `Role.permissions` (JSON) implementa la matriz de `docs/permisos-roles.md` tal cual: mapa de área → `ver/editar/sin_acceso`.
- Clase base de permiso en `core/permissions.py` que **niega por defecto**; cada `ViewSet` declara qué área y qué nivel necesita.
- Mixin de alcance por objeto (`core/querysets.py`) que todo selector de app futura reutiliza: nunca se filtra comparando el `id` de la URL contra el usuario, siempre se filtra el queryset desde el usuario autenticado hacia abajo (sección 14.2) — esta es la pieza más sensible de toda la fase y la que más prueba de acceso no autorizado necesita.
- `GET /students/{id}/sensitive/` usa un serializer separado, alcanzable solo por `DIR` (editar) y `ADMIN` (ver) — ya no hay ni modelo `Student` todavía en esta fase (llega en la Fase 5), así que aquí solo se deja la clase de permiso genérica lista y su prueba de contrato, sin el endpoint real todavía.

## 7. Bitácora y registro de acceso (RNF-06, RNF-07)

- `core.AuditLog`: modelo de solo escritura (ADR-0004). Se expone un helper `registrar_cambio(user, entity, action, old, new)` en `core/services.py` que las futuras apps importarán desde sus propios `services/` — no se usa como señal de Django.
- `core.AccessLog`: middleware ligero que registra `usuario, fecha, pantalla consultada` en cada petición autenticada a la API (no en peticiones anónimas, salvo la de verificación por QR que se trata aparte en la Fase 9).
- `GET /audit-log/` y `GET /access-log/` (contrato ya fijado) quedan operativos desde esta fase, aunque con poco que mostrar hasta que existan más módulos.

## 8. Semilla de datos de esta fase

Comando `seed_fase3` (no el comando de demostración completo de la sección 16, que llega cuando existan más módulos): crea los 8 roles de `docs/permisos-roles.md` con sus permisos, y un usuario de cada rol con contraseña de siembra ficticia, para poder probar login y permisos de punta a punta sin datos reales.

## 9. Pruebas previstas (de `docs/trazabilidad.md`)

- `test_rf01_crear_usuario_asigna_rol.py`
- Suite de acceso no autorizado por rol (sección 16): un usuario de cada rol contra un endpoint que no le corresponde.
- `test_rnf03_control_acceso_por_rol.py`
- `test_rnf04_aislamiento_datos_familia.py` (estructura del mixin, aunque `Student`/`Guardian` no existan aún, se prueba contra un modelo de fixture)
- `test_rnf05_bloqueo_por_intentos_fallidos.py`, `test_rnf05_expiracion_sesion_inactividad.py`
- `test_rnf06_bitacora_registra_cambio.py`
- `test_rnf07_registro_acceso_se_genera.py`
- `frontend/e2e/iniciar-sesion.spec.ts` (uno de los seis flujos de la sección 16, el primero que ya se puede probar)

## 10. Orden de trabajo

1. Estructura de carpetas + configuración por entornos + `.env.example` (sin lógica todavía).
2. CI mínimo (falla en verde con un proyecto vacío) antes de agregar código, para que cada commit posterior ya corra en un pipeline real.
3. `core`: `AuditLog`, `AccessLog`, permisos base, middleware de registro de acceso.
4. `accounts`: `Role`, `User`, autenticación completa.
5. Biblioteca de componentes base del frontend + tokens de la Propuesta B.
6. Semilla `seed_fase3` + pruebas de la sección 9.
7. Flujo de Playwright de inicio de sesión.

Commits pequeños, `feat:`/`chore:`/`test:`/`ci:`, en la rama `fase-03-cimientos`.

## Punto de control

Antes de escribir el primer archivo de código de esta fase, falta:

1. **Confirmar ADR-0007** (JWT, esquema OpenAPI, CORS) — es lo único que bloquea literalmente empezar, porque el primer `requirements/base.txt` depende de esta decisión.
2. Luz verde para crear la estructura de repositorio de la sección 1.
