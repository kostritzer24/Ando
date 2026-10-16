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

## Segunda ronda: prueba guiada E2E (15/10/2026)

El equipo siguió `docs/guia-prueba-e2e.html` y anotó 23 fallos más los hallazgos de los demás (`docs/resultados-prueba-e2e.md`). Se corrigió en la misma rama.

### Decisiones del dueño

| Tema | Decisión | Dónde quedó |
|---|---|---|
| Roles | Se eliminan «Docente con sección a cargo» y «Administrador del sistema». Cualquier docente levanta reportes de conducta y responde el buzón en las secciones donde da clase o es docente a cargo; las respuestas dicen quién respondió | Migración `accounts/0002`; `permisos-roles.md` |
| Cuotas | Mensualidad Q100 en básico y Q150 en bachillerato; inscripción Q200 por ciclo. El sistema pone el monto y el recibo (automático) | `payments/domain/fees.py`, `payments/services/payment.py`, migración `payments/0002` |
| Becas | Solo completa o ninguna; una beca completa no genera cobros | Migración `catalog/0003`, seed |
| Talleres | La inscripción a un taller es de la misma persona: se agrega o se saca desde el expediente, y cambiar de grado mueve la misma inscripción (no se crea otro estudiante) | `students/services/enrollment.py`, `InscripcionesPanel.vue` |

### Hallazgo → corrección

| Hallazgo | Causa | Corrección |
|---|---|---|
| Pantallas con error al entrar que se arreglan recargando; «Sección» y «Beca» solo con «Ninguna»; 403 en `/users/` | Dos ventanas comparten la cookie de refresco: al renovarse el token una ventana se volvía, sin avisar, el otro usuario. Además `opcional()` escondía el 403 | `authStore`/`http.ts`: confirman que la persona sigue siendo la misma tras renovar y las demás ventanas se enteran de un inicio o cierre de sesión. Secciones ya no pide `/users/` de forma obligatoria |
| Coordinación no abre Secciones | La pantalla exigía la lista de usuarios (403) | Lista de docentes opcional |
| Cruces de horario intermitentes | Las clases de asignaciones dadas de baja seguían ocupando celdas; mover un bloque no se validaba; volver a asignar chocaba con la unicidad | `schedule_block.py`, `teacher_assignment.py`: solo cuentan bloques y asignaciones vigentes del ciclo; baja lógica que libera celdas; reactivación; `PATCH` validado |
| Mensaje en inglés al duplicar una asignación | Validador de unicidad de DRF | «X ya tiene asignado Y en esa sección» |
| Secciones duplicadas | Sin validación | `SectionSerializer.validate` |
| Fechas de nacimiento absurdas | Solo se rechazaba más de 100 años | Edad entre 4 y 25 años |
| Horarios de talleres | Solo existían los períodos de la mañana | Franja de la tarde (períodos 7 a 11, de 14:00 a 19:00) para talleres; los cursos usan 1 a 6 |
| Horario en PDF y en cuadrícula | Solo había una lista | `GET /reports/schedule-grid/` (JSON y PDF) por grado o por persona; pantalla de Reportes y de Horario |
| Horario más fácil | — | La grilla marca celdas libres y no disponibles y permite repetir un curso en varios días |
| María Ximena aparece dos veces en Pagos | Se listaban también las inscripciones de taller | Pagos solo lista la inscripción de grado; la solvencia de un taller es la del grado |
| Documentos descargan con el código como nombre | `Content-Disposition` usaba el código de verificación | «Tipo - Estudiante.pdf» (UTF-8) |
| Justificaciones confusas; un archivo bajó sin formato en una computadora | No se explicaba que primero hay que marcar «ausente»; el nombre de respaldo no tenía extensión y el tipo era `octet-stream` | Texto guía, faltas ya justificadas fuera de la lista, tipo y nombre correctos en la descarga y extensión de respaldo |
| Buzón rompe la vista móvil con palabras largas | Texto sin `overflow-wrap` | Conversación en burbujas, con nombre y cargo, que parte palabras largas |
| Avisos muy blancos | — | Tarjetas de color con franja lateral |
| Selectores gigantes | `<select>` con decenas de opciones | `FormBuscador` (búsqueda con predicción) en estudiantes, vínculos, asignaciones, horario y reportes de conducta |
| «Secciones de distintos años» indistinguibles | Etiqueta sin año | El año del ciclo en las etiquetas (`cycle_year`) |

### Sin cambio o por confirmar

- **Contraseña provisional como definitiva:** el backend ya la rechazaba (`test_cambiar_la_contrasena_por_la_misma_se_rechaza`); probablemente se probó con un servidor sin la corrección de la fase anterior. Re-probar.
- **Tallerista marcando asistencia de otro taller:** el backend ya lo impide por asignación (pruebas en `test_rf21...` y `test_rf16...`); probablemente se asignaron varios talleres a `tallerista.demo`. Re-probar con una base nueva.
- **Horarios de la tarde:** decisión del dueño: los talleres van de 14:00 a 19:00; se modelaron como cinco períodos de una hora.
- **Inscripción de Q200:** decisión del dueño: sin la inscripción pagada el estudiante no es solvente (y no se emite la constancia), salvo beca completa.
