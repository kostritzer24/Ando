# Arquitectura y mapa de módulos

Arquitectura por capas fijada en la sección 12 del prompt maestro: dependencia en un solo sentido (presentación → aplicación → dominio → datos), con una capa transversal (`core/`) para lo que ninguna app posee en exclusiva. Este documento fija qué vive en cada módulo del backend y del frontend, para que el mapeo con RF y con la matriz de trazabilidad (`docs/trazabilidad.md`) sea directo.

## 1. Regla de capas (recordatorio operativo)

Dentro de cada app de Django:

```
apps/<modulo>/
├── api/        # views, serializers, routers, permissions, filtros — sin lógica de negocio
├── services/   # un caso de uso por operación, transacciones, escribe la bitácora
├── domain/     # reglas de negocio puras (las 17 RN viven aquí)
├── selectors/  # querysets de lectura para listados y reportes
├── models.py   # modelos, managers, constraints, índices
└── tests/
```

Dos verificaciones en cada revisión de código: una vista no importa un modelo directamente para escribir, y un modelo no llama a un servicio.

## 2. Apps del backend

| App | Entidades que contiene | Responsabilidad |
|---|---|---|
| `accounts` | Usuario, Rol | Autenticación (JWT), gestión de cuentas, permisos por rol. RF-01, RNF-03, RNF-05. |
| `core` | Bitácora de cambios, Registro de acceso | Transversal: auditoría, registro de acceso, generación de PDF y QR, lectura/escritura de plantillas, manejo de errores, paginación, permisos de objeto reutilizables. RNF-06, RNF-07, sección 14. |
| `catalog` | Ciclo escolar, Unidad, Sección, Curso, tipos de actividad/justificación/documento, Beca | Los siete datos maestros parametrizables (sección 9). RF-02. |
| `students` | Estudiante, Encargado, `GuardianStudentLink`, Inscripción | Expedientes, vínculo familiar, inscripción — el núcleo del modelo. RF-03, RF-04. |
| `scheduling` | Asignación docente, Bloque de horario, Evento de calendario | Asignaciones, horario con validación de cruces, calendario semanal. RF-05, RF-06, RF-22, RF-26. |
| `attendance` | Asistencia, Justificación | Registro diario y por plantilla, justificaciones y su resolución. RF-16, RF-12, RF-21. |
| `grading` | Actividad, Calificación, Modificación de nota | Definición de actividades, punteo real, cálculo de notas, plantillas, modificaciones, boletines. RF-17 a RF-20, RF-23, RF-10, RF-09 (generación). |
| `payments` | Pago, Beca (persistencia) | Pagos, solvencia, constancias. RF-07, RF-08. |
| `documents` | Documento emitido | Emisión, código QR, verificación pública. RF-11, RF-14. |
| `communication` | Aviso, Reporte de conducta, Mensaje de buzón | Cartelera, conducta, buzón con filtro de palabras. RF-13, RF-24, RF-25, RNF-10. |
| `reports` | (sin modelos propios; consume selectores de las demás apps) | Las 8 consultas institucionales y el reporte de métricas del estudio. RF-15. |

`grading` agrupa boletines junto con actividades y calificaciones (en vez de una app `report_cards` separada) porque la elegibilidad del boletín (RN-09 + RN-10) depende directamente de las mismas reglas de dominio que calculan la nota — separarlas obligaría a duplicar esa lógica entre dos apps, justo el riesgo técnico 6 señalado en la Fase 0.

## 3. Mapa de features del frontend

```
src/
├── app/            # arranque, router, guards por rol, interceptores de Axios (refresh de token)
├── pages/
│   ├── administrativo/   # Dirección, Coordinación, Encargado de pagos, Administrador
│   ├── operativo/          # Docente, Docente con sección a cargo, Tallerista
│   └── publico/            # Padre de familia
├── features/
│   ├── auth/                  # login, selector de estudiante (HU-27)
│   ├── catalogo/               # administración de los 7 datos maestros
│   ├── estudiantes/            # expedientes, vínculos, inscripción
│   ├── horarios/                # armado de horario, calendario semanal
│   ├── asistencia/               # registro diario, plantilla de talleres, justificaciones
│   ├── notas/                     # actividades, plantilla de calificaciones, modificaciones, boletín
│   ├── pagos/                      # pagos, solvencia, constancias
│   ├── documentos/                  # emisión, verificación por QR (única ruta pública sin sesión)
│   ├── calendario/                   # calendario semanal como pantalla de entrada del portal público
│   ├── avisos/                        # cartelera
│   ├── buzon/                          # mensajería asincrónica por hilo
│   └── reportes/                        # las 8 consultas + métricas
├── shared/         # componentes de interfaz, utilidades, tipos comunes derivados del esquema OpenAPI
└── design/         # tokens de la Fase 2, estilos base, tipografía
```

Cada `features/<feature>/` sigue el patrón `api/ components/ composables/ stores/` de la sección 12.2 del prompt maestro. Un componente de presentación nunca llama a `axios` directamente; toda llamada pasa por `features/<feature>/api/`.

## 4. Contrato entre backend y frontend

- API REST bajo `/api/v1/`, un router por app de Django.
- Esquema OpenAPI generado automáticamente desde DRF (`drf-spectacular` o equivalente — a decidir en ADR cuando se llegue a la Fase 3, ya que no está fijado en el stack de la sección 13).
- Los tipos de TypeScript del frontend se generan desde ese esquema; no se escriben a mano (sección 12.3 del prompt maestro).
- El contrato de endpoints propuesto está en `docs/api.md`.

## 5. Rutas por portal (guard de router)

| Prefijo de ruta | Portal | Roles permitidos |
|---|---|---|
| `/administrativo/*` | Administrativo | Dirección, Coordinación, Encargado de pagos, Administrador del sistema |
| `/operativo/*` | Operativo | Docente, Docente con sección a cargo, Tallerista |
| `/portal/*` | Público | Padre de familia |
| `/verificar/:codigo` | Público, sin sesión | Cualquiera — única ruta sin autenticación, RF-14 |

Es una sola aplicación de página única (sección 2 del prompt maestro): los tres portales comparten `app/router` y el guard decide qué rama de rutas exponer según el rol del token, no son despliegues separados.
