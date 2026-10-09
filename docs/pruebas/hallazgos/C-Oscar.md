# Hallazgos — Set C — Oscar Geovany

Fecha: 2026-10-06 · Rama/commit probado: `fase-15-formatos-institucionales @ f39e883` (con `main` ya integrado) · Navegador: Chromium (Playwright) · SO: Windows 11

## Leer primero, corrector

- **C-001 a C-020 ya están corregidos.** Esta revisión se hizo antes de conocer el plan de pruebas y terminó en correcciones de código: PR #3 `fix/notas-integridad`, ya en `main`. Después `main` se integró en esta rama y se resolvió el conflicto del boletín (quedó el formato institucional).
  - El detalle de cada corrección y sus pruebas está en `docs/revision-notas-boletines.md`.
  - **No hay que corregirlos de nuevo, solo volver a probarlos.**
- **C-021 a C-024 siguen abiertos.**
- **Hay una decisión pendiente para el dueño del proyecto** (al final): RN-05 quedó implementada con plazo de entrega, y eso contradice el resultado esperado de NOT-10 y PLN-04.
- **Cómo se encontraron:** con pruebas exploratorias contra la API real (temporales, ya borradas) y pruebas automatizadas. No es una pasada manual en el navegador; lo que falta de eso está marcado ⏭️ en la cobertura.

---

## Corregidos en `main` (volver a probar)

### C-001 · Una nota registrada se podía borrar por la API y registrar de nuevo con otro valor

- **Caso del plan:** `NOT-10`
- **Tipo:** seguridad · datos
- **Severidad:** Crítica
- **Rol con el que ocurrió:** docente.demo
- **Dónde:** `DELETE /api/v1/grades/{id}/`
- **Referencia:** RN-05; baja lógica (sección 8.5)
- **Pasos para reproducir:**
  1. Como docente, registrar una nota.
  2. Mandar `DELETE /api/v1/grades/{id}/` con su token.
  3. Registrar otra vez la misma actividad con otro punteo.
- **Esperado:** la nota no se puede borrar; cualquier cambio pasa por una solicitud a Dirección.
- **Obtenido:** 204, la fila se borraba de verdad, y la nota nueva entraba sin autorización.
- **Reproducible:** siempre
- **Evidencia:** prueba `test_rn05_una_nota_no_se_puede_borrar_por_la_api`
- **Viewport:** n/a (API)
- **Hipótesis de causa:** `GradeViewSet` era un `ModelViewSet` completo. **Corregido:** ahora solo crea y consulta (405).

### C-002 · Una nota se podía mover a otra actividad o a otro estudiante

- **Caso del plan:** `NOT-10`
- **Tipo:** datos
- **Severidad:** Crítica
- **Rol con el que ocurrió:** docente.demo
- **Dónde:** `PATCH /api/v1/grades/{id}/`
- **Referencia:** RN-05
- **Pasos para reproducir:** `PATCH /api/v1/grades/{id}/` con `{"activity": "<otra actividad>"}`
- **Esperado:** rechazado.
- **Obtenido:** 200, la nota quedaba en otra actividad.
- **Reproducible:** siempre
- **Evidencia:** prueba `test_rn05_una_nota_no_se_puede_editar_ni_mover_a_otra_actividad`
- **Viewport:** n/a
- **Hipótesis de causa:** la misma que C-001. **Corregido.**

### C-003 · Un docente podía calificar a un estudiante de otra sección

- **Caso del plan:** fuera de plan (relacionado con `NOT-05`)
- **Tipo:** permisos · datos
- **Severidad:** Crítica
- **Rol con el que ocurrió:** docente.demo
- **Dónde:** `POST /api/v1/grades/`
- **Referencia:** HU-05, RNF-04
- **Pasos para reproducir:** `POST /grades/` con una actividad propia y la inscripción de un estudiante de otra sección.
- **Esperado:** 400.
- **Obtenido:** 201.
- **Reproducible:** siempre
- **Evidencia:** prueba `test_rf18_no_se_califica_a_un_estudiante_de_otra_seccion`
- **Viewport:** n/a
- **Hipótesis de causa:** solo se validaba que la asignación fuera del docente, no la inscripción. **Corregido.**

### C-004 · El tope de 100 puntos se podía pasar editando el punteo máximo

- **Caso del plan:** `NOT-02`
- **Tipo:** bug
- **Severidad:** Alta
- **Rol con el que ocurrió:** docente.demo
- **Dónde:** `PATCH /api/v1/activities/{id}/`
- **Referencia:** RN-01, RN-02
- **Pasos para reproducir:**
  1. Crear una unidad con dos actividades de 50 puntos.
  2. Hacer PATCH a una de ellas con `max_score: 90`.
- **Esperado:** rechazado.
- **Obtenido:** 200; la unidad quedó en 140 puntos.
- **Reproducible:** siempre
- **Evidencia:** prueba `test_rn02_editar_el_maximo_no_puede_pasar_los_cien_puntos`
- **Viewport:** n/a
- **Hipótesis de causa:** el tope solo se validaba al crear. **Corregido.**

### C-005 · Desactivar una actividad calificada dejaba una nota de unidad de 150

- **Caso del plan:** `NOT-03`
- **Tipo:** datos
- **Severidad:** Alta
- **Rol con el que ocurrió:** docente.demo
- **Dónde:** `PATCH /api/v1/activities/{id}/` con `is_active: false`
- **Referencia:** RN-01
- **Pasos para reproducir:**
  1. Calificar una actividad.
  2. Desactivarla por PATCH.
  3. Crear otra de 50 puntos y calificarla.
- **Esperado:** no se puede dar de baja una actividad con notas.
- **Obtenido:** la nota de unidad del estudiante quedó en 150.
- **Reproducible:** siempre
- **Evidencia:** pruebas `test_rn01_una_actividad_calificada_no_se_da_de_baja` y `test_rn01_la_nota_de_unidad_no_cuenta_actividades_dadas_de_baja`
- **Viewport:** n/a
- **Hipótesis de causa:** `is_active` se podía editar, y `nota_de_unidad` no ignoraba las actividades dadas de baja. **Corregido.**

### C-006 · Una plantilla con columnas movidas, de otra unidad o desactualizada guardaba los punteos en la actividad equivocada

- **Caso del plan:** `PLN-03`
- **Tipo:** datos
- **Severidad:** Crítica
- **Rol con el que ocurrió:** docente.demo
- **Dónde:** /operativo/notas/plantilla
- **Referencia:** HU-19, HU-20, RF-20
- **Pasos para reproducir:**
  1. Descargar la plantilla de una unidad con dos actividades.
  2. Intercambiar dos columnas (o usar la plantilla de otra unidad, o una descargada antes de agregar una actividad).
  3. Cargarla.
- **Esperado:** error de estructura; no se guarda nada.
- **Obtenido:** 201; los punteos quedaron cruzados entre actividades, sin ningún error.
- **Reproducible:** siempre
- **Evidencia:** pruebas `test_hu20_*` en `test_rf19_rf20_rn07_plantilla_notas.py`
- **Viewport:** escritorio
- **Hipótesis de causa:** las columnas se leían por posición sin comparar encabezados. **Corregido:** hoja oculta de identidad, validación de encabezados y celdas de código y nombre bloqueadas.

### C-007 · Una plantilla con un código repetido daba error 500 y dejaba notas guardadas a medias

- **Caso del plan:** `PLN-03`, `PLN-05`
- **Tipo:** bug · datos
- **Severidad:** Crítica
- **Rol con el que ocurrió:** docente.demo
- **Dónde:** `POST /api/v1/grades/template/upload/`
- **Referencia:** RF-20
- **Pasos para reproducir:** cargar una plantilla con el mismo código en dos filas.
- **Esperado:** error por fila; no se guarda nada.
- **Obtenido:** 500; se guardaron 2 notas.
- **Reproducible:** siempre
- **Evidencia:** prueba `test_rf20_codigo_repetido_es_un_error_de_fila_y_no_guarda_nada`
- **Viewport:** n/a
- **Hipótesis de causa:** la carga no estaba en una transacción. **Corregido.**

### C-008 · Un archivo que no es Excel daba error 500, y no había límite de tamaño

- **Caso del plan:** `PLN-03`
- **Tipo:** bug · seguridad
- **Severidad:** Alta
- **Rol con el que ocurrió:** docente.demo
- **Dónde:** `POST /api/v1/grades/template/preview/`
- **Referencia:** sección 14.4
- **Pasos para reproducir:** cargar un archivo `notas.xlsx` que no sea un Excel real, o uno de varios MB.
- **Esperado:** 400 con un mensaje claro.
- **Obtenido:** 500.
- **Reproducible:** siempre
- **Evidencia:** pruebas `test_rf20_un_archivo_que_no_es_excel_responde_400_no_500` y `test_rf20_rechaza_un_archivo_demasiado_pesado`
- **Viewport:** n/a
- **Hipótesis de causa:** **Corregido** (400 y límite de 2 MB).

### C-009 · Una solicitud de corrección ya rechazada se podía aprobar después

- **Caso del plan:** `MOD-06`
- **Tipo:** bug
- **Severidad:** Alta
- **Rol con el que ocurrió:** dir.demo
- **Dónde:** `POST /api/v1/grade-change-requests/{id}/approve/`
- **Referencia:** RF-10, RN-05
- **Pasos para reproducir:**
  1. Rechazar una solicitud.
  2. Aprobarla.
- **Esperado:** 400, "ya fue resuelta".
- **Obtenido:** 200; la nota cambió.
- **Reproducible:** siempre
- **Evidencia:** prueba `test_rn05_una_solicitud_ya_rechazada_no_se_puede_aprobar_despues`
- **Viewport:** n/a
- **Hipótesis de causa:** **Corregido**, con bloqueo de fila.

### C-010 · Dos solicitudes pendientes sobre la misma nota se pisaban entre sí

- **Caso del plan:** `MOD-06`
- **Tipo:** datos
- **Severidad:** Alta
- **Rol con el que ocurrió:** docente.demo y dir.demo
- **Dónde:** /administrativo/notas/modificaciones
- **Referencia:** RF-23, RF-10
- **Pasos para reproducir:**
  1. Pedir una corrección a 9.
  2. Pedir otra a 2 sobre la misma nota.
  3. Aprobar las dos.
- **Esperado:** no se permite una segunda solicitud mientras haya una pendiente.
- **Obtenido:** se aceptaron ambas; la nota quedó en la última que se aprobó.
- **Reproducible:** siempre
- **Evidencia:** prueba `test_rf23_no_se_abre_una_segunda_solicitud_mientras_hay_una_pendiente`
- **Viewport:** n/a
- **Hipótesis de causa:** **Corregido.**

### C-011 · La "nota original" de una solicitud mostraba el punteo real, no la nota vigente

- **Caso del plan:** `MOD-03`
- **Tipo:** datos · ux
- **Severidad:** Media
- **Rol con el que ocurrió:** dir.demo
- **Dónde:** /administrativo/notas/modificaciones
- **Referencia:** RF-10
- **Pasos para reproducir:**
  1. Aprobar una corrección de 6 a 9.
  2. Pedir otra corrección sobre la misma nota.
- **Esperado:** la segunda muestra 9 como nota original.
- **Obtenido:** muestra 6; Dirección decide con un dato incorrecto.
- **Reproducible:** siempre
- **Evidencia:** prueba `test_rf23_la_nota_original_de_una_solicitud_es_la_vigente`
- **Viewport:** escritorio
- **Hipótesis de causa:** **Corregido.**

### C-012 · Ningún cambio de notas o boletines quedaba en la bitácora

- **Caso del plan:** `MOD-03`
- **Tipo:** falta-funcionalidad
- **Severidad:** Alta
- **Rol con el que ocurrió:** cualquiera
- **Dónde:** /administrativo/bitacora
- **Referencia:** RNF-06, ADR-0004
- **Pasos para reproducir:** registrar una nota, aprobar una corrección o publicar un boletín, y abrir la Bitácora.
- **Esperado:** cada cambio aparece con usuario, valor anterior y valor nuevo.
- **Obtenido:** 0 registros. Lo mismo pasaba con asistencia (Set B).
- **Reproducible:** siempre
- **Evidencia:** pruebas `test_rnf06_*`
- **Viewport:** escritorio
- **Hipótesis de causa:** **Corregido**, también para asistencia.

### C-013 · Rechazar una corrección no pedía motivo

- **Caso del plan:** `MOD-02`
- **Tipo:** falta-funcionalidad
- **Severidad:** Media
- **Rol con el que ocurrió:** dir.demo
- **Dónde:** /administrativo/notas/modificaciones
- **Referencia:** RF-10
- **Pasos para reproducir:** clic en "Rechazar".
- **Esperado:** pide el motivo, y el docente lo ve.
- **Obtenido:** se rechazaba sin motivo y sin confirmación.
- **Reproducible:** siempre
- **Evidencia:** prueba `test_rf10_rechazar_sin_motivo_no_se_acepta_y_con_motivo_lo_ve_el_docente`
- **Viewport:** escritorio
- **Hipótesis de causa:** **Corregido.**

### C-014 · El boletín publicado cambiaba si después se aprobaba una corrección de nota

- **Caso del plan:** `BOL-06`
- **Tipo:** datos
- **Severidad:** Alta
- **Rol con el que ocurrió:** dir.demo, familia.demo
- **Dónde:** `/api/v1/report-cards/{id}/download/`
- **Referencia:** RF-09, RF-34
- **Pasos para reproducir:**
  1. Publicar un boletín.
  2. Aprobar una corrección de una de sus notas.
  3. Descargarlo otra vez.
- **Esperado:** el documento entregado no cambia en silencio.
- **Obtenido:** se recalculaba con la nota nueva.
- **Reproducible:** siempre
- **Evidencia:** prueba `test_rf09_el_boletin_aprobado_no_cambia_si_despues_se_corrige_una_nota`
- **Viewport:** n/a
- **Hipótesis de causa:** **Corregido:** el contenido se congela al aprobar.

### C-015 · Se podía aprobar un boletín con notas faltantes sin aviso (y Tercero básico sale vacío)

- **Caso del plan:** `NOT-11`, `BOL-01`
- **Tipo:** ux · datos
- **Severidad:** Media
- **Rol con el que ocurrió:** dir.demo
- **Dónde:** /administrativo/boletines
- **Referencia:** RF-09
- **Pasos para reproducir:**
  1. Generar los boletines de una sección con notas incompletas, o de Tercero básico, que en `seed_demo` no tiene cursos asignados.
  2. Aprobar.
- **Esperado:** se avisa qué falta antes de aprobar.
- **Obtenido:** se aprobaba sin aviso; el boletín de Tercero básico quedaba vacío.
- **Reproducible:** siempre
- **Evidencia:** pruebas `test_rf09_el_listado_muestra_los_cursos_con_notas_pendientes` y `test_rf09_una_seccion_sin_cursos_asignados_queda_marcada_como_pendiente`
- **Viewport:** escritorio
- **Hipótesis de causa:** **Corregido:** columna "Notas" con los pendientes y confirmación antes de aprobar.

### C-016 · Las pantallas de notas descargaban todos los datos, y la API hacía una consulta por fila

- **Caso del plan:** `NOT-12`
- **Tipo:** rendimiento
- **Severidad:** Media
- **Rol con el que ocurrió:** docente.demo, dir.demo
- **Dónde:** Capturar notas, Modificaciones, Boletines
- **Referencia:** RNF-01 (conexión lenta)
- **Pasos para reproducir:** listar 60 notas por la API.
- **Esperado:** pocas consultas, y las pantallas piden solo lo que muestran.
- **Obtenido:** 363 consultas. Las pantallas traían todas las notas, inscripciones y estudiantes y filtraban en el navegador.
- **Reproducible:** siempre
- **Evidencia:** prueba `test_listar_notas_no_hace_una_consulta_por_fila`
- **Viewport:** n/a
- **Hipótesis de causa:** **Corregido:** `select_related` y filtros en el servidor. **No probado con `seed_masivo`.**

### C-017 · En Capturar notas, un error al guardar escondía la lista y no decía el motivo

- **Caso del plan:** `TRV-03`
- **Tipo:** ux
- **Severidad:** Media
- **Rol con el que ocurrió:** docente.demo
- **Dónde:** /operativo/notas/capturar
- **Referencia:** sección 15.2
- **Pasos para reproducir:** escribir un punteo mayor que el máximo.
- **Esperado:** el motivo, junto a la lista, sin perder lo demás.
- **Obtenido:** el banner reemplazaba la lista y mostraba un mensaje genérico; el campo no tenía mínimo ni máximo.
- **Reproducible:** siempre
- **Evidencia:** revisión del código de `CapturarNotasPage.vue`
- **Viewport:** escritorio
- **Hipótesis de causa:** **Corregido.**

### C-018 · En Modificaciones, aprobar no pedía confirmación y un error no se avisaba

- **Caso del plan:** `TRV-02`, `TRV-03`
- **Tipo:** ux
- **Severidad:** Media
- **Rol con el que ocurrió:** dir.demo
- **Dónde:** /administrativo/notas/modificaciones
- **Referencia:** sección 15.2
- **Pasos para reproducir:** aprobar una solicitud que otra persona ya resolvió.
- **Esperado:** aviso y la lista recargada.
- **Obtenido:** la promesa quedaba sin manejar; no aparecía nada.
- **Reproducible:** siempre
- **Evidencia:** revisión del código de `ModificacionesPage.vue`
- **Viewport:** escritorio
- **Hipótesis de causa:** **Corregido.**

### C-019 · Los boletines solo se aprobaban y publicaban de uno en uno

- **Caso del plan:** `BOL-01`
- **Tipo:** ux
- **Severidad:** Mejora
- **Rol con el que ocurrió:** dir.demo
- **Dónde:** /administrativo/boletines
- **Referencia:** RF-09
- **Pasos para reproducir:** aprobar y publicar los boletines de una sección de 30 estudiantes.
- **Esperado:** acción por lote.
- **Obtenido:** 60 clics por sección y unidad.
- **Reproducible:** siempre
- **Evidencia:** —
- **Viewport:** escritorio
- **Hipótesis de causa:** **Corregido:** botones de lote, con la lista de quién quedó sin publicar y por qué.

### C-020 · Una actividad mal creada no se podía editar ni quitar

- **Caso del plan:** `NOT-03`
- **Tipo:** falta-funcionalidad
- **Severidad:** Media
- **Rol con el que ocurrió:** docente.demo
- **Dónde:** /operativo/notas/unidad
- **Referencia:** RF-17
- **Pasos para reproducir:** crear una actividad con un error y buscar cómo corregirla.
- **Esperado:** editar o quitar mientras no tenga notas.
- **Obtenido:** no había botones.
- **Reproducible:** siempre
- **Evidencia:** —
- **Viewport:** escritorio
- **Hipótesis de causa:** **Corregido:** editar y quitar; quitar solo sin notas, y con baja lógica.

---

## Abiertos (sin corregir)

### C-021 · El mensaje de plazo del boletín no dice desde qué fecha se puede publicar

- **Caso del plan:** `BOL-03`
- **Tipo:** texto
- **Severidad:** Media
- **Rol con el que ocurrió:** dir.demo
- **Dónde:** /administrativo/boletines → Publicar
- **Referencia:** RN-10
- **Pasos para reproducir:**
  1. Aprobar el boletín de una unidad cuya fecha de habilitación todavía no llegó.
  2. Publicar.
- **Esperado:** "se puede publicar a partir del dd/mm/aaaa", con la fecha exacta (lo pide el plan).
- **Obtenido:** "Todavía no se cumple el plazo para habilitar el boletín (RN-10)." No dice la fecha, y además muestra un código interno (RN-10).
- **Reproducible:** siempre
- **Evidencia:** `backend/apps/grading/domain/report_card.py`, `validar_publicacion`
- **Viewport:** escritorio
- **Hipótesis de causa (hipótesis):** la validación de dominio recibe solo un booleano `plazo_cumplido`, no la fecha. Lo mismo pasa con "(RN-09)" en el mensaje de insolvencia.

### C-022 · El cuadro de notas muestra 0 en un curso sin notas en una unidad visible, y ese 0 entra al promedio

- **Caso del plan:** `NOT-11`, `BOL-05`
- **Tipo:** datos · pdf
- **Severidad:** Alta
- **Rol con el que ocurrió:** familia.demo (PDF), dir.demo
- **Dónde:** PDF del boletín
- **Referencia:** RN-02, RN-03
- **Pasos para reproducir:**
  1. Tener un curso de la sección sin ninguna actividad ni nota en la unidad.
  2. Aprobar y publicar el boletín de esa unidad.
  3. Descargar el PDF.
- **Esperado:** la celda queda vacía o dice que no hay nota; no cuenta como 0 en el promedio ni marca "R".
- **Obtenido:** la celda muestra 0, entra al promedio del curso y a la fila "Promedio de Unidad", y puede marcar "R".
- **Reproducible:** siempre
- **Evidencia:** `services/report_card.py`, `contenido_boletin`: una unidad visible sin notas aporta `calcular_nota_unidad([])` = 0. Ya era así en `fase-15` antes de integrar `main`.
- **Viewport:** n/a
- **Hipótesis de causa (hipótesis):** `armar_fila_cuadro` deja en blanco solo los `None`, pero el servicio nunca pasa `None` para una unidad visible. La bandeja de boletines ya avisa de estos pendientes antes de aprobar (C-015), pero el PDF sigue mostrando el 0 sin aclarar nada.

### C-023 · (K-2) Dirección no tiene dónde ver las notas, ni el boletín antes de aprobarlo

- **Caso del plan:** `BOL-09` (K-2)
- **Tipo:** falta-funcionalidad
- **Severidad:** Alta
- **Rol con el que ocurrió:** dir.demo
- **Dónde:** portal administrativo
- **Referencia:** RF-09, RF-10, RN-05
- **Lo que ve hoy un director:**
  - "Boletines": la lista por sección y unidad con su estado y los pendientes. No se puede abrir un boletín: el PDF solo se descarga cuando ya está **publicado**.
  - "Modificaciones de notas": solo las solicitudes de corrección.
  - No hay ninguna pantalla de notas por sección, curso o estudiante. Capturar notas y Diseñar unidad están en el portal operativo, para docentes.
- **Lo que esperaría ver:**
  1. Una vista **"Notas por sección"**: elegir sección y unidad, y ver la tabla de estudiantes × cursos con la nota de unidad, las actividades de cada curso y qué falta calificar.
  2. Desde un estudiante, su cuadro completo (las 4 unidades y el promedio): lo mismo que verá la familia.
  3. En la bandeja de boletines, **"Ver boletín"** en borrador y aprobado: la vista previa del PDF antes de aprobarlo. Hoy se aprueba a ciegas, y como el contenido se congela al aprobar, un error queda fijo.
  4. Corregir: según RN-05, Dirección no edita la nota directamente. Desde la vista de notas debería poder abrir o autorizar una corrección (que hoy solo pide el docente).
- **Reproducible:** siempre
- **Evidencia:** `frontend/src/app/router.ts`: las rutas del administrativo para notas son solo `boletines` y `notas/modificaciones`. `download/` exige estado publicado (`grading/api/views.py`).
- **Viewport:** escritorio
- **Propuesta:** requiere decisión del dueño del proyecto, porque no está como RF explícito. Lo mínimo y más urgente es el punto 3, la vista previa antes de aprobar: aprobar congela el contenido.

### C-024 · No hay forma de despublicar ni revertir un boletín

- **Caso del plan:** `BOL-07`
- **Tipo:** falta-funcionalidad
- **Severidad:** Mejora
- **Rol con el que ocurrió:** dir.demo
- **Dónde:** /administrativo/boletines
- **Referencia:** no documentado
- **Pasos para reproducir:** publicar un boletín con un error y buscar cómo retirarlo.
- **Esperado:** documentar si debería existir. Si se aprueba con un error, hoy no hay salida.
- **Obtenido:** no existe ninguna acción para despublicar o volver a borrador, ni en la API ni en la pantalla.
- **Reproducible:** siempre
- **Evidencia:** no existe una acción `unpublish` ni una transición inversa en `domain/report_card.py`.
- **Viewport:** escritorio
- **Hipótesis de causa:** no se diseñó. Es una decisión del dueño, ligada a C-023 (vista previa) y C-014 (contenido congelado).

---

## Decisión pendiente para el dueño del proyecto

**RN-05 con plazo de entrega** (afecta el resultado esperado de **NOT-10** y **PLN-04**).
- **Cómo quedó en `main`:** hasta la fecha de entrega de notas de la unidad (`grades_due_date`), el docente corrige directamente su nota (`POST /grades/{id}/correct/`), con bitácora y sin tocar el punteo real. Después de esa fecha, solo con autorización de Dirección. La plantilla recargada sigue el mismo corte.
- **Por qué se hizo así:** el texto literal de RN-05 pide autorización siempre, y entonces un error de dedo queda fijo hasta que Dirección lo apruebe. Eso contradice la sección 15.2.
- **Si no se acepta:** revertirlo es acotado. Se quitan `correct/` y la acción "corrección" de la plantilla.

---

## Cobertura de mi set

✅ pasó · ❌ falló (ver hallazgo) · ⏭️ no se pudo probar (motivo)

| Caso | Estado | Hallazgo(s) |
|---|---|---|
| NOT-01 | ✅ | e2e `notas` (total en vivo) |
| NOT-02 | ❌ | C-004 (corregido). Pesos 0 y negativos ✅ por API |
| NOT-03 | ❌ | C-005, C-020 (corregidos) |
| NOT-04 | ⏭️ | Sin regla documentada; ver "cosas raras" |
| NOT-05 | ✅ | Pruebas de aislamiento por rol; tallerista sin acceso |
| NOT-06 | ✅ | e2e `notas` |
| NOT-07 | ⏭️ | Rango 0..máximo ✅ por API; la coma decimal ("7,5") en el navegador no se probó |
| NOT-08 | ⏭️ | Redondeo .5 ✅ en dominio (59.5 → 60); no comparado a mano entre pantalla, boletín y reportes |
| NOT-09 | ✅ | Pruebas de `scoring` (59, 59.5, 60) |
| NOT-10 | ❌ | C-001, C-002 (corregidos) + decisión RN-05 |
| NOT-11 | ❌ | C-015 (corregido), C-022 (abierto) |
| NOT-12 | ❌ / ⏭️ | C-016 (corregido); no probado con `seed_masivo` |
| PLN-01 | ✅ | e2e + prueba de hoja protegida |
| PLN-02 | ✅ | Probado contra el servidor real |
| PLN-03 | ❌ | C-006, C-007, C-008 (corregidos) |
| PLN-04 | ✅ / decisión | Después del plazo genera una solicitud ✅; dentro del plazo corrige directo (decisión RN-05) |
| PLN-05 | ✅ | Recargar la misma plantilla no genera nada |
| MOD-01 | ✅ | e2e `notas` |
| MOD-02 | ❌ | C-013 (corregido) |
| MOD-03 | ❌ | C-011, C-012 (corregidos) |
| MOD-04 | ✅ / ⏭️ | Por API ✅ (sin `raw_score` ni solicitudes para la familia); en el portal no se revisó a mano |
| MOD-05 | ✅ | Pruebas de permisos |
| MOD-06 | ❌ | C-009, C-010 (corregidos) |
| BOL-01 | ✅ | e2e `pagos-documentos-boletines` (+ C-019) |
| BOL-02 | ✅ | e2e, mensaje de RN-09 |
| BOL-03 | ❌ | C-021 (abierto) |
| BOL-04 | ✅ | Pruebas de dominio y de API |
| BOL-05 | ❌ / ⏭️ | C-022 (abierto). No se revisó visualmente el PDF institucional (logo, QR, líneas de firma) |
| BOL-06 | ❌ | C-014 (corregido: ahora no cambia) |
| BOL-07 | ❌ | C-024 (abierto) |
| BOL-08 | ✅ | e2e `portal-publico` + pruebas |
| BOL-09 | ❌ | C-023 (abierto, K-2) |
| BOL-10 | ✅ | Pruebas de permisos |
| TRV-01…09, 11…13 | ⏭️ | Pasada manual en el navegador pendiente: móvil 375 px, backend caído, doble clic, consola, teclado, PDF |
| TRV-10 | ❌ | Se encontraron errores 500 → C-007, C-008 (corregidos) |
| K-3 | ⏭️ | No revisado |

## Cosas que me parecieron raras pero no estoy seguro de que sean error

- **NOT-04:** se pueden crear actividades y registrar notas **nuevas** en una unidad ya cerrada. RN-07 solo habla de la plantilla recargada después del cierre (modificaciones), no de notas que faltaban. Hoy entran directo, con bitácora. ¿Es lo correcto? Es decisión del dueño.
- **Mensajes que muestran códigos internos** ("(RN-09)", "(RN-10)"): se le muestran a Dirección. ¿Deberían quitarse? (Relacionado con C-021.)
- **Mínimo de 4 pruebas cortas (RN-04):** el sistema solo lo muestra como aviso en "Diseñar unidad", no lo exige. El PROMPT_MAESTRO lo describe como práctica institucional, así que parece correcto, pero conviene confirmarlo.
