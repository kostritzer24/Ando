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

## Hecho

- **Fase 3** — Login, cambio de contraseña obligatorio, guards de router por rol. (`frontend/src/features/auth/`)
