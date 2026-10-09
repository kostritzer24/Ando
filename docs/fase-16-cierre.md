# Fase 16 — Correcciones de la ronda de pruebas manuales

Rama: `fase-16-correcciones-pruebas`. El estado de cada hallazgo está en `docs/pruebas/triage.md`.

## Qué se hizo

Cuatro testers (sets A–D) probaron a mano. Un solo corrector hizo el triage y corrigió por lotes, cada uno con pruebas.

| Lote | Contenido | Commits |
|---|---|---|
| 0 | Seguridad: familia veía insolventes ajenos (A-001), nómina de taller sin asignación (B-001) | `f16593c`, `1ba6b8b` |
| 1 | Integridad: asistencia duplicada, `DELETE` real, pantallas rotas por 403, buzón bloqueado | `1ba6b8b`, `7d5efc2`, `e9f86f7`, `2241e07` |
| 2 | Decisiones del dueño: sin "tarde" ni hora, asistencia global, familia solo ve nota total, baja de estudiante | `d525c05`, `49bfa43` |
| 3 | Validaciones: fechas, duplicados, cruces de horario, justificaciones, selectores sin inactivos | `92d0ec8`, `214e1ca` |
| 3b | Vista previa del boletín para Dirección | `42d481b` |
| 4 | UX: 404, fechas legibles, nombres de archivo, receso, semanas, accesos con nombre de pantalla, salud al inscribir, filtros en Pagos | `75093be`, `146d4d6` |

Además: textos de la interfaz sin códigos RN/RF y con tono neutro tipo Drive (tuteo, sin voseo).

## Causas raíz que se repitieron

- **Permisos por área demasiado gruesos**: un reporte institucional detrás de un área que la familia también tiene (A-001); catálogos de solo lectura detrás de un área que el rol no tenía (A-005, D-005).
- **Validar solo en la interfaz**: fechas, duplicados y roles se comprobaban en el formulario y no en la API.
- **Errores tragados**: nueve diálogos descartaban el motivo del servidor.
- **Cabeceras CORS**: `Content-Disposition` no estaba expuesta, así que todas las descargas se llamaban igual.

## Verificación en vivo

- Backend: `ruff`, `pytest` y cobertura de `domain/` y `services/` ejecutados al cierre.
- E2E (Playwright, orden documentado en `CLAUDE.md`, base reseteada): los 14 specs pasan. Specs nuevos: `pantallas-de-solo-lectura`, `formularios-y-cuenta-nueva`.
- Se arregló `seed_masivo` (estaba roto) y los specs con fechas fijas.
- `portal-publico` necesita base propia; no forma parte de esta corrida.

## Pendiente (decide el dueño o falta medir)

A-003 (emitir documento sin bitácora), B-009, B-014, C-024 y vista "Notas por sección", D-003, D-006, D-008, D-011, D-013; la carrera de recargas en ráfaga de la sesión (K-1); las "cosas raras" de Gabriela listadas en el triage.

Decisión del dueño: la asistencia del taller es aparte de la de la mañana. Ya lo cumple el modelo (una asistencia por inscripción y día; el taller tiene su propia inscripción).

## Qué debe re-probar cada tester

Reiniciar la base antes: `cd backend && rm db.sqlite3 && python manage.py migrate && python manage.py seed_demo`.

- **A (Francisco):** A-001 con `familia.demo` sobre insolventes, unidades con fechas cruzadas, nombres de curso duplicados, contraseña igual, bitácora (columna Pantalla), ruta inexistente.
- **B (Gabriela):** nómina de taller sin asignación, asistencia en fin de semana o futura (y que ya no hay "tarde" ni hora), justificaciones repetidas, nombre del archivo de plantilla, receso en el horario, semanas en el portal, fechas legibles.
- **C (Oscar):** que sus C-001 a C-020 sigan bien, curso sin notas ("—" y fuera del promedio), mensaje de plazo con fecha, "Ver boletín" antes de aprobar.
- **D (Milton):** buzón bloqueado y filtro con números, "Ver vínculos", bandeja de documentos, datos de salud al inscribir, dar de baja, filtros en Pagos.
