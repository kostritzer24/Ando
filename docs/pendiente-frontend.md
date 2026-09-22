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

## Hecho

- **Fase 3** — Login, cambio de contraseña obligatorio, guards de router por rol. (`frontend/src/features/auth/`)
