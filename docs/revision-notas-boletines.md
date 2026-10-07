# Revisión: Notas (unidad, captura, plantilla, modificaciones) y boletines

Rama `fix/notas-integridad`. Revisión hecha del 5 al 6 de octubre de 2026.

## Alcance y criterio

Se revisaron las cuatro partes de la sección:

- **Diseño de la unidad.**
- **Captura de notas.**
- **Plantilla de calificaciones.**
- **Modificaciones y boletines.**

En cada una se revisó el backend (`backend/apps/grading/`), el frontend (`frontend/src/features/notas/` y `BoletinesPage.vue`) y sus pruebas.

El criterio no fue solo "¿cumple el PROMPT_MAESTRO?", sino **"¿está bien implementado según buenas prácticas de desarrollo?"**: integridad de datos, diseño de la API, transacciones, auditoría, rendimiento, seguridad, experiencia de uso y calidad de las pruebas. Donde el PROMPT_MAESTRO no lleva a la mejor solución, se señala.

**Método:**
1. Se leyó el código.
2. Cada sospecha se **reprodujo contra la API real** con pruebas exploratorias temporales, ya borradas. Ningún hallazgo de este documento es solo una suposición.
3. Se corrigió.
4. Cada corrección quedó con una prueba que fallaba antes y pasa después.

## Veredicto inicial

- **Boletines:** bien diseñados en lo esencial.
- **Captura de notas:** no estaba lista para producción. El modelo de datos era sólido (separa el punteo real de la nota vigente), pero la API permitía hacer lo que ese modelo pretendía impedir. Además, el flujo de captura era frágil ante errores humanos y no escalaba.
- **Pruebas:** las 381 pasaban porque solo cubrían los caminos previstos, no los endpoints que habían quedado abiertos de más.

---

## 1. Hallazgos graves: integridad de datos

| # | Hallazgo | Evidencia | Regla o práctica afectada |
|---|---|---|---|
| 1.1 | Un docente podía **borrar una nota** y volver a registrarla con otro valor, saltando la autorización de Dirección. El borrado era real, no lógico | `DELETE /grades/{id}/` → 204 | RN-05; baja lógica en todo el sistema |
| 1.2 | Una nota se podía **mover a otra actividad o a otro estudiante** | `PATCH /grades/{id}/` → 200 | La identidad de un registro no se edita |
| 1.3 | Se podía **calificar a un estudiante de otra sección** en una actividad propia | `POST /grades/` → 201 | Validar las relaciones entre entidades, no solo el permiso |
| 1.4 | **El tope de 100 puntos se podía evadir**: solo se validaba al crear | Un PATCH del máximo dejó la unidad en **140**; desactivar y crear otra dejó una nota de unidad de **150** | RN-01/RN-02 |
| 1.5 | La plantilla con **columnas movidas, de otra unidad o desactualizada** guardaba punteos **en la actividad equivocada, sin error** | Columnas invertidas → 201 con los valores cruzados | HU-19/HU-20 |
| 1.6 | La plantilla con un **código repetido** daba **error 500** y dejaba 2 notas guardadas a medias | Probado | Operaciones por lote en una transacción |
| 1.7 | Dos **solicitudes pendientes** sobre la misma nota se aprobaban ambas y ganaba la última | La nota quedó en 2 tras aprobar 9 y luego 2 | Concurrencia y estados |
| 1.8 | La "nota original" de una solicitud mostraba el punteo real, no la nota vigente | Mostró 6 cuando la vigente era 9 | Dirección decidía con información incorrecta |
| 1.9 | Una solicitud **ya rechazada se podía aprobar** después | Rechazar → 200 y luego aprobar → 200 | Máquina de estados |
| 1.10 | Notas, actividades, solicitudes, boletines **y asistencia** no escribían nada en la **bitácora** | 0 registros | RNF-06; ADR-0004; `docs/seguridad.md` afirmaba lo contrario |

**Causa común de 1.1 a 1.4:** `GradeViewSet` y `ActivityViewSet` eran `ModelViewSet` genéricos, que abren PUT, PATCH y DELETE sin pasar por los servicios. Es el mismo error que la Fase 14 de UI/UX ya había corregido en `/users/`. Además, ningún servicio de notas usaba transacciones ni bloqueos.

## 2. Hallazgos de diseño (donde el PROMPT_MAESTRO o el diseño no eran lo mejor)

| # | Hallazgo | Por qué importa |
|---|---|---|
| 2.1 | **RN-05 aplicada desde el primer dígito.** Cada punteo quedaba definitivo al salir del campo, así que un error de dedo exigía una solicitud a Dirección | Contradice la propia sección 15.2: *"guardar las notas de toda una sección sin poder corregir un error de dedo es inaceptable"* |
| 2.2 | **El boletín publicado cambiaba después de publicado**: se recalculaba en cada descarga | Un documento oficial debe ser inmutable una vez entregado |
| 2.3 | **Se podía aprobar un boletín con notas faltantes** sin saberlo; las faltantes contaban como 0 | El boletín mostraba como definitiva una nota parcial |
| 2.4 | Marcaba **"Reprobado" por unidad** y no mostraba las unidades anteriores ni el promedio | RN-03 define la aprobación del **curso** por la nota final, no por unidad |
| 2.5 | `validar_unidad_completa` decía validarse "antes de registrar punteo", pero **nadie la llamaba**, y exigía un mínimo de 4 pruebas cortas | Código muerto y engañoso. El propio PROMPT_MAESTRO dice que las pruebas cortas son "práctica institucional"; no deberían ser un bloqueo |

## 3. Hallazgos de arquitectura y rendimiento

| # | Hallazgo | Evidencia |
|---|---|---|
| 3.1 | **N+1**: listar notas hacía unas 6 consultas por fila | 60 notas → **363 consultas** |
| 3.2 | **Sin filtros en el servidor**: Capturar notas, Modificaciones y Boletines descargaban todas las notas, inscripciones, estudiantes y boletines visibles, y filtraban en el navegador | Crece con cada año de datos, en un sistema que exige funcionar con conexión lenta |
| 3.3 | La plantilla subida solo se validaba por extensión: sin límite de tamaño, y un archivo corrupto daba 500 | Riesgo de "bomba zip" en `.xlsx` |

## 4. Hallazgos de experiencia de uso

| # | Pantalla | Hallazgo |
|---|---|---|
| 4.1 | Capturar notas | Un error al guardar **reemplazaba la lista completa** por el banner y se perdía lo escrito; el mensaje era genérico aunque el servidor decía el motivo exacto; el campo no tenía mínimo ni máximo |
| 4.2 | Modificaciones | Aprobar o rechazar no pedía confirmación; un fallo no se avisaba (promesa sin manejar); no había **motivo del rechazo**; para armar una línea de contexto se descargaban cinco listas completas |
| 4.3 | Boletines | Aprobar y publicar **de a uno** (30 estudiantes eran 60 clics por sección y unidad); no se veía qué faltaba antes de aprobar |
| 4.4 | Diseñar unidad | Una actividad mal creada **no se podía corregir ni quitar** |

## 5. Hallazgo encontrado durante la verificación

| # | Hallazgo |
|---|---|
| 5.1 | En la siembra, **Tercero básico no tiene ningún curso asignado**: su boletín salía **vacío** y el sistema no lo marcaba |

---

## Cambios aplicados

### Backend

**API cerrada y validaciones en los servicios** (1.1–1.4)
- `/grades/` solo crea y consulta: PUT, PATCH y DELETE responden 405.
- `registrar_punteo` exige que el estudiante esté inscrito en la sección y el ciclo de la actividad.
- Actividades:
  - Editar pasa por `actualizar_actividad`, que vuelve a validar el tope, y la asignación y la unidad ya no se pueden mover.
  - Una actividad con notas no cambia su máximo ni se da de baja.
  - La baja es lógica (`dar_de_baja_actividad`).
  - `is_active` ya no se puede editar por PATCH.
- `nota_de_unidad` ignora las actividades dadas de baja.

**Solicitudes de modificación** (1.7–1.9, 4.2)
- Reglas puras en `domain/grade_change.py`:
  - una sola solicitud pendiente por nota;
  - el punteo propuesto debe estar en rango y ser distinto del vigente;
  - solo se resuelve una solicitud pendiente.
- `original_score` es la nota vigente al pedir la corrección.
- Al resolver se bloquea la fila (`select_for_update`).
- Rechazar exige el motivo (`resolution_note`), que el docente ve en su bandeja.
- Cada solicitud trae su contexto (estudiante, curso, unidad, actividad y nota vigente).

**Plantilla** (1.5, 1.6, 3.3)
- La plantilla lleva una hoja oculta `_plantilla` con la asignación, la unidad y las actividades en orden de columna. Se rechaza un archivo que no la tenga, que sea de otro curso o unidad, o que esté desactualizado.
- Se validan los encabezados, para detectar columnas movidas, borradas o agregadas.
- Código y nombre quedan bloqueados en Excel; el código va con formato de texto para que no pierda los ceros a la izquierda.
- Un código repetido es un error de fila.
- La carga es todo o nada (`transaction.atomic`).
- Archivo ilegible → 400; límite de 2 MB.

**Bitácora** (1.10)
- Se escribe en la misma transacción que el cambio en:
  - creación y corrección de notas;
  - actividades (crear, editar y dar de baja);
  - solicitudes (crear y resolver);
  - boletines (generar, aprobar y publicar);
  - asistencia (registrar, y el cambio de estado al aprobar una justificación).

**RN-05 con plazo de entrega** (2.1). Ver "Decisión a validar" más abajo.
- `POST /grades/{id}/correct/`: hasta `grades_due_date` inclusive, el docente corrige directamente la nota vigente. Queda en bitácora y el punteo real no cambia.
- Después de esa fecha, solo por solicitud.
- La plantilla recargada sigue el mismo corte: dentro del plazo cuenta como "corrección", después como "modificación".

**Boletines** (2.2–2.4, 4.3, 5.1)
- Al aprobar se **congela** el contenido (`ReportCard.contenido`); eso es lo que se publica y se descarga.
- El contenido sigue el **formato institucional "Cuadro de notas"** que trajo `fase-15-formatos-institucionales`: las cuatro unidades, promedio final, A/R, promedio de unidad y firma del maestro guía, con solo las unidades ya publicadas más la actual. Ese formato es el documento real del centro, así que reemplazó la primera versión de esta revisión ("unidades hasta la actual + nota final solo en la cuarta"). Solo incluye cursos académicos (ADR-0001).
- `grading/selectors/avance.py` calcula por lote, para cada boletín, los cursos con notas faltantes, las unidades que no suman 100 o una sección sin cursos, con un detalle legible.
- `approve-batch` y `publish-batch`. La publicación en lote informa quién quedó sin publicar y por qué (RN-09/RN-10).

**Rendimiento** (3.1, 3.2)
- `select_related` en los ViewSets de notas, actividades, solicitudes, boletines e inscripciones.
- Filtros por `public_id`, siempre aplicados *después* del alcance del usuario:
  - `/grades/?activity&assignment&unit&enrollment`
  - `/activities/?assignment&unit`
  - `/report-cards/?section&unit`
  - `/enrollments/?section`
  - `/grade-change-requests/?status`
- `/enrollments/` trae `student_name` y `student_code`.

**Código muerto** (2.5): la regla de "mínimo 4 pruebas cortas" se deja como aviso en la pantalla de la unidad (ya lo era), no como bloqueo. Lo que sí importa, que la unidad sume 100, se informa en los pendientes del boletín.

**Migración:** `grading/0003_boletin_congelado_y_motivo_de_decision`, con dos campos opcionales. Un boletín publicado antes de esta migración se sigue descargando; su contenido se calcula en el momento.

### Frontend

- **Capturar notas:**
  - pide solo la sección y la actividad elegidas;
  - dentro del plazo corrige en el mismo campo; fuera del plazo ofrece "Solicitar corrección";
  - el campo valida de 0 al máximo;
  - avisa hasta qué fecha se puede corregir;
  - un error muestra el motivo real sin esconder la lista.
- **Modificaciones:**
  - el contexto viene del servidor;
  - aprobar confirma la nota de antes y la de después;
  - rechazar pide el motivo en un diálogo;
  - si alguien más ya la resolvió, se avisa y la lista se recarga.
- **Boletines:**
  - lista filtrada en el servidor;
  - una columna "Notas" con lo que falta;
  - aprobar con pendientes pide confirmación;
  - "Aprobar los N borradores" y "Publicar los N aprobados", con la lista de quién quedó sin publicar.
- **Diseñar unidad:**
  - editar y quitar actividades;
  - el motivo del rechazo aparece dentro del diálogo.
- **Plantilla:** la vista previa y el resultado muestran las correcciones directas.
- **Bitácora:** etiquetas legibles para las entidades y los campos nuevos.
- **Contrato:** `api.ts` regenerado contra el backend.

### Documentación

`docs/api.md` está al día con los endpoints, los filtros y el comportamiento nuevo.

---

## Decisión a validar con Dirección del centro

**RN-05 con plazo de entrega.** El texto literal pide autorización de Dirección para *cualquier* cambio de nota. Se implementó así:
- hasta la fecha de entrega de notas de la unidad, el docente corrige directamente, con bitácora y sin tocar el punteo real;
- después de esa fecha, solo con autorización.

Se eligió así por tres razones:
- la sección 15.2 considera inaceptable no poder corregir un error de dedo;
- RN-07 ya usa el cierre como punto de corte para la plantilla;
- las notas pasan a ser oficiales en la entrega (RN-10), no en el momento de teclearlas.

**Si Dirección no lo acepta, revertirlo es acotado:** se quitan `correct/` y la acción `correccion` de la plantilla, y `puede_corregirse_sin_autorizacion` pasa a devolver siempre `False`.

## Lo que está bien hecho (se conserva)

- Separar el punteo real de la nota vigente (`raw_score` / `current_score`). El punteo real nunca se expone en la API (RN-06).
- `Decimal` en todos los cálculos y una sola función de redondeo documentada (ADR-0003).
- Máquina de estados del boletín con dominio puro y probado.
- Plazos de RN-10 calculados automáticamente y de solo lectura.
- Solvencia verificada al publicar (RN-09).
- La familia solo ve los boletines publicados de sus propios hijos.
- La plantilla separa vista previa de carga.
- El PDF se genera bajo demanda.

## Integración con `fase-15-formatos-institucionales`

Esta revisión se hizo sin conocer el plan de pruebas en equipo de `fase-15` (`docs/pruebas/`), donde este trabajo correspondía al **Set C (tester)** y las correcciones a un único corrector. `fix/notas-integridad` se integró a `main` (PR #3) antes que `fase-15` (PR #2), y las dos ramas modificaban los mismos 4 archivos del boletín.

El conflicto se resolvió integrando `main` en `fase-15`:
- **Formato del boletín:** el de `fase-15`.
- **Del trabajo de esta revisión se conserva:** contenido congelado al aprobar, aprobación y publicación en lote, bitácora, solo cursos académicos y la consulta por lote.

Para el corrector:
- Los hallazgos de este documento ya están corregidos en `main`.
- RN-05 con plazo de entrega (que contradice el resultado esperado de NOT-10 y PLN-04 del plan) queda como **decisión pendiente del dueño del proyecto**.

## Fuera de alcance, con motivo

- **Autorización por nombre de rol** en `grading/api/views.py`: todas las apps del proyecto usan el mismo patrón. Cambiarlo solo aquí rompería la consistencia sin ganar nada; si se hace, que sea en todo el proyecto a la vez.

---

## Verificación

| Qué | Resultado |
|---|---|
| Pruebas de backend | **453** pasan (381 antes); ruff y `ruff format --check` limpios |
| Cobertura de `domain/` y `services/` (grading + attendance) | **97 %** |
| Frontend | lint, typecheck, 51 pruebas y build sin errores |
| E2E (Chromium, base recién sembrada) | Las **12 specs** de la cadena documentada en su orden: **38 pruebas en verde** |
| E2E `portal-publico` (en su propia base) | Pasa |
| Navegador, con una spec temporal ya borrada | Editar y quitar actividad; aprobar y publicar en lote |
| Servidor real | Descargar, llenar y cargar la plantilla, incluidos los rechazos (encabezado alterado, código duplicado, archivo armado a mano) |

### Dónde están las pruebas

| Tema | Archivo |
|---|---|
| API cerrada, inscripción ajena, tope de 100 al editar, bitácora, consultas | `backend/apps/grading/tests/test_rn05_rnf06_integridad_notas.py` |
| Corrección en plazo, motivo de rechazo, boletín congelado, unidades y nota final, pendientes, lote, filtros | `backend/apps/grading/tests/test_rn05_rf09_plazo_y_boletin.py` |
| Identidad de la plantilla, encabezados, duplicados, archivo ilegible o pesado | `backend/apps/grading/tests/test_rf19_rf20_rn07_plantilla_notas.py` |
| Reglas puras de solicitudes, plazo, identidad y filas del boletín | `backend/apps/grading/domain/tests/test_rf23_rf10_grade_change.py`, `test_hu19_hu20_identidad_plantilla.py`, `test_formatear_nota.py` |
| Bitácora de asistencia | `backend/apps/attendance/tests/test_rf16_rn11_asistencia_diaria_tardanza.py`, `test_rf12_rn12_justificacion_falta.py` |
| Filtro y nombre en inscripciones | `backend/apps/students/tests/test_rnf04_aislamiento_inscripciones_por_rol.py` |

### Commits

| Commit | Contenido |
|---|---|
| `7411634` | La API respeta RN-05, el tope de 100 y la bitácora |
| `cbdb35c` | Mensajes del servidor y confirmación al resolver correcciones |
| `6d2fba2` | Corrección dentro del plazo, boletín congelado y en lote, filtros, bitácora de asistencia |
| `cbd41de` | Pantallas al día con el contrato nuevo |
