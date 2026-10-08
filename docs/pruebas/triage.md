# Triage de la ronda de pruebas manuales (octubre 2026)

Cuatro testers probaron el sistema a mano (sets A–D). Este documento junta sus hallazgos, dice qué se hizo con cada uno y qué sigue abierto. Los IDs son los originales de cada archivo en `docs/pruebas/hallazgos/`.

Rama de trabajo: `fase-16-correcciones-pruebas`. Los commits citados son de esa rama.

## Decisiones del dueño que cambiaron requisitos

| Tema | Decisión | Efecto |
|---|---|---|
| Corrección de notas (RN-05) | El docente corrige directo hasta la fecha de entrega; después, solo con Dirección | Se deja como estaba en `main` |
| Asistencia (RN-11, HU-16) | Se elimina "tarde" y la hora de llegada. La asistencia es una por estudiante y día, no por clase | `d525c05`; el `PROMPT_MAESTRO.md` y `modelo-datos.md` lo reflejan |
| Portal de familia | Solo la nota total por curso y unidad | `49bfa43`; la API ya no manda detalle por actividad ni docente |
| Pagos | No se anulan ni se corrigen | D-014 cerrado sin cambios |
| Estudiantes | Se pueden dar de baja | `49bfa43` |
| Boletines | Nada sale sin que Dirección lo revise y apruebe | `42d481b`: vista previa antes de aprobar |

## Resultado por hallazgo

**Estados:** corregido · ya estaba corregido (Oscar, PR #3) · decisión del dueño · no reproducible / no es bug · abierto.

### Set A (Francisco)

| ID | Resumen | Estado |
|---|---|---|
| A-001 | Familia veía insolventes de otras familias (Crítica) | Corregido `f16593c` |
| A-002 | La bitácora no registraba notas ni asistencia | Ya estaba corregido (C-012); asistencia se audita en `d525c05` |
| A-003 | Emitir un documento no queda en la bitácora de cambios | **Abierto** (Media) |
| A-004 | Unidades con fechas invertidas o cruzadas | Corregido `92d0ec8` |
| A-005 | Pantallas rotas por 403 (Coordinación y Pagos) | Corregido `e9f86f7` |
| A-006 | Catálogos con nombres duplicados | Corregido `92d0ec8` (cursos; los demás catálogos ya tenían nombre único) |
| A-007 | Rutas inexistentes en blanco | Corregido `75093be` |
| A-008 | Selectores ofrecían registros dados de baja | Corregido `92d0ec8` |
| A-009 | Contraseña nueva igual a la actual | Corregido `92d0ec8` |
| A-010 | Accesos con rutas técnicas | Corregido `146d4d6` |
| A-011 | `127.0.0.1` no permite iniciar sesión | No es bug: cookie `SameSite=Strict`, documentado en `LEEME.md` |
| K-1 | La sesión no persiste | Ver nota al final |

### Set B (Gabriela)

| ID | Resumen | Estado |
|---|---|---|
| B-001 | Nómina de taller descargable sin asignación (Crítica) | Corregido `1ba6b8b` |
| B-002 | Fecha de nacimiento futura o absurda | Corregido `92d0ec8` |
| B-003 | Evento con fin antes del inicio o en el pasado | Corregido `92d0ec8` |
| B-004 | Asistencia en sábado, domingo o fecha futura | Corregido `92d0ec8` |
| B-005 | Fecha de hoy en UTC después de las 6 pm | Corregido `92d0ec8` |
| B-006 | Varias justificaciones sobre la misma falta | Corregido `92d0ec8` |
| B-007 | Asistencia duplicada daba 500 | Corregido `1ba6b8b` |
| B-008 | Justificación resuelta se podía re-resolver | Corregido `92d0ec8` |
| B-009 | Un docente no ve eventos de otro de su sección | **Abierto**: no está documentado, decide el dueño |
| B-010 | Inscribir no mostraba el motivo del error | Corregido `214e1ca` (9 pantallas) |
| B-011 | Fechas en formato ISO | Corregido `75093be` |
| B-012 | Mensaje técnico al subir un archivo que no es Excel | Corregido `75093be` |
| B-013 | Plantilla descargada como `plantilla.xlsx` | Corregido `75093be` (encabezado CORS no expuesto) |
| B-014 | RN-12 (pérdida de derecho) no se ve en pantalla | **Abierto**: decisión del dueño |
| B-015 | Falta el receso en la grilla del horario | Corregido `75093be` |
| B-016 | ✕ del horario desaparece en celular | Corregido `75093be` (sin ver a 375 px) |
| B-017 | Familia sin navegación entre semanas | Corregido `75093be` |
| B-018 | `DELETE` borraba de verdad | Corregido `7d5efc2` |
| B-019 | Portal sin hijos: cargando infinito | Corregido `214e1ca` |
| B-020 | `PATCH` de asignación no revalidaba el rol | Corregido `92d0ec8` |
| B-021 | Dos cursos en la misma sección, día y período | Corregido `92d0ec8` |

Notas de Gabriela sin hallazgo propio (sección "cosas raras"), pendientes: plantilla de talleres sin celdas protegidas, `DELETE` de asignación con evento da 500 por `PROTECT`, `PATCH is_active` responde 200 sin cambiar, `?is_active=true` ignorado en `/sections/`, F5 pierde la sección y fecha elegidas en asistencia, no hay forma de abrir el expediente desde asistencia, el formulario de encargado no pide correo.

### Set C (Oscar)

| ID | Resumen | Estado |
|---|---|---|
| C-001 a C-020 | Integridad de notas, plantillas, solicitudes, boletín congelado, rendimiento | Ya corregidos (PR #3). Re-probar |
| C-021 | Mensaje de plazo sin fecha | Corregido `75093be` |
| C-022 | Curso sin notas aparecía como 0 y entraba al promedio | Corregido `75093be` |
| C-023 | Dirección no puede revisar el boletín antes de aprobar | Corregido `42d481b` (vista previa). La vista "Notas por sección" **queda abierta** |
| C-024 | No se puede despublicar un boletín | **Abierto**: decisión del dueño (relacionado con C-023) |

### Set D (Milton)

| ID | Resumen | Estado |
|---|---|---|
| D-001 | El bloqueo del buzón no impedía enviar | Corregido `2241e07` |
| D-002 | Filtro evadible con números | Corregido `2241e07` (no cubre `p.u.t.a`) |
| D-003 | Mensajes del buzón en los dos hijos | **Abierto**: el mensaje no guarda el estudiante, solo la sección |
| D-004 | "Ver vínculos" no mostraba nada | Corregido `75093be` |
| D-005 | Bandeja de documentos vacía | Corregido `e9f86f7` (causa: 403 en tipos de documento) |
| D-006 | Pago sin tope de monto | **Abierto**: no hay mensualidad documentada, decide el dueño |
| D-007 | Pago de enero "duplicado" | Descartado por el propio tester |
| D-008 | Aprobar cambio de nota tarda ~1 minuto | **Abierto**: sin reproducir ni medir |
| D-009 | Salud solo después de inscribir | Corregido `146d4d6` |
| D-010 | Campo de hora en asistencia | Resuelto al eliminar la hora (`d525c05`) |
| D-011 | Fecha de entrega pasada al diseñar actividad | **Abierto**: no documentado |
| D-012 | Evento termina antes de empezar | Corregido `92d0ec8` |
| D-013 | Reportes con fechas futuras | **Abierto**: los reportes filtran por ciclo y sección, no por fechas |
| D-014 | No se puede anular un pago | Decisión del dueño: no se anulan |
| D-015 | Pagos sin filtros | Corregido `146d4d6` (sección y búsqueda) |
| D-016 | No hay baja de estudiante | Corregido `49bfa43` |

### Nota sobre K-1 y ACC-07 (sesión)

Francisco aisló que la sesión sí persiste y que solo falla con recargas en ráfaga (rotación y lista negra del refresh). Gabriela vio un 401 `Token is expired` tras 15 minutos. Revisé `frontend/src/app/http.ts`: un 401 dispara una renovación silenciosa y reintenta la petición, así que el 401 que se ve en la pestaña Network es el paso normal previo. Es una lectura del código, **no se probó en vivo** con 15 minutos de espera. La carrera de recargas en ráfaga **sigue abierta** (Francisco la reprodujo).

### Hallazgos nuevos encontrados al corregir

- `seed_masivo` estaba roto: `crear_actividad` pedía `usuario` y los boletines de la Unidad 1 nunca se publicaban.
- Los specs de Playwright con fechas fijas (`2026-03-10`) se rompían con las validaciones nuevas.
- `comunicacion` bloquea a `familia.demo` 24 h; cualquier spec que la use debe correr antes.
