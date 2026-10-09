# Hallazgos — Set D — Milton Meren

Fecha: 2026-10-05 · Rama/commit probado: `fase-15-formatos-institucionales @ 1f92784` · Navegador: Chrome · SO: Windows 11

Base local: `seed_demo` + `seed_masivo`. Los hallazgos D-008 a D-013 son de pantallas de otros sets; los anoto porque los encontré, para que el corrector los cruce con A, B y C.

---

### D-001 · El bloqueo del buzón (RN-16) no impide seguir enviando mensajes

- **Caso del plan:** `BUZ-04`
- **Tipo:** seguridad
- **Severidad:** Alta
- **Rol con el que ocurrió:** familia.demo
- **Dónde:** /portal → Buzón
- **Referencia:** RN-16, RNF-10
- **Pasos para reproducir:**
  1. Con familia.demo, enviar un mensaje con una palabra de la lista (p. ej. "puta").
  2. Aparece "no se envió y tu cuenta quedó bloqueada temporalmente".
  3. Sin cerrar sesión, enviar otro mensaje (cualquiera).
- **Esperado:** con la cuenta bloqueada no se puede enviar nada hasta que termine el bloqueo.
- **Obtenido:** el segundo mensaje se envía y se guarda.
- **Reproducible:** siempre
- **Evidencia:** en la base local, `familia.demo.locked_until = 2026-10-07 04:44:50 UTC` (el bloqueo empezó el 2026-10-06 04:44:50 UTC), y después existe el mensaje `subject='revision', content='put0'` creado el **2026-10-06 04:45:37 UTC**, 47 s después del bloqueo.
- **Viewport:** escritorio
- **Hipótesis de causa:** `locked_until` solo se revisa al iniciar sesión (`backend/apps/accounts/services/auth.py:32`). `enviar_mensaje` y `responder_mensaje` (`backend/apps/communication/services/buzon.py:16`, `:28`) no lo revisan, y el JWT y el refresh ya emitidos siguen siendo válidos durante el bloqueo.

---

### D-002 · El filtro de lenguaje se evade cambiando una letra por un número

- **Caso del plan:** `BUZ-04` / `BUZ-05`
- **Tipo:** seguridad
- **Severidad:** Media
- **Rol con el que ocurrió:** familia.demo
- **Dónde:** /portal → Buzón
- **Referencia:** RNF-10, RN-16
- **Pasos para reproducir:**
  1. Enviar un mensaje con "put0" (una "o" cambiada por cero).
- **Esperado:** el filtro lo detecta igual que "puta"/"puto".
- **Obtenido:** se envía sin aviso (es el mismo mensaje de la evidencia de D-001).
- **Reproducible:** siempre
- **Evidencia:** mensaje `content='put0'` guardado en la base.
- **Viewport:** escritorio
- **Hipótesis de causa:** `backend/apps/communication/domain/buzon.py:34` separa las palabras con `[a-z]+`, así que "put0" queda como "put" y no coincide. Lo mismo pasaría con "1diota", "m1erda", "p.u.t.a", etc. Ojo: el código dice que la lista es "una primera barrera, no exhaustiva"; decidir cuánto endurecerlo (normalizar 0→o, 1→i, 3→e, 4→a, quitar puntos y espacios) sin causar falsos positivos (BUZ-05).

---

### D-003 · En el portal, los mensajes del buzón aparecen en los dos hijos

- **Caso del plan:** `BUZ-07` / `POR-01` / `POR-10`
- **Tipo:** bug
- **Severidad:** Media
- **Rol con el que ocurrió:** familia.demo (2 estudiantes vinculados)
- **Dónde:** /portal → Buzón, cambiando de estudiante con el selector
- **Referencia:** HU-27 ("toda la información cambia con el estudiante"), RF-37
- **Pasos para reproducir:**
  1. Con familia.demo, elegir el hijo 1 y enviar un mensaje al buzón.
  2. Cambiar al hijo 2 con el selector.
- **Esperado:** el buzón muestra solo los hilos de la sección del estudiante seleccionado.
- **Obtenido:** los mismos mensajes aparecen con los dos hijos.
- **Reproducible:** siempre
- **Evidencia:** los 2 mensajes de familia.demo están en la sección "Segundo básico" y se ven en ambos hijos.
- **Viewport:** escritorio
- **Hipótesis de causa:** `MessageViewSet.scope_queryset` (`backend/apps/communication/api/views.py:206`) devuelve todos los hilos del encargado, sin filtrar por sección o estudiante, y el portal no filtra por el hijo seleccionado. Si los dos hijos están en la misma sección, decidir cómo se distingue (el mensaje no guarda el estudiante, solo la sección).

---

### D-004 · "Ver vínculos" de un encargado no muestra nada

- **Caso del plan:** fuera de plan (pantalla de estudiantes y encargados)
- **Tipo:** ux
- **Severidad:** Media
- **Rol con el que ocurrió:** dir.demo
- **Dónde:** /administrativo → Encargados → botón "Ver vínculos"
- **Referencia:** RF-04
- **Pasos para reproducir:**
  1. Abrir Encargados.
  2. Presionar "Ver vínculos" en cualquier encargado.
- **Esperado:** se ven los estudiantes vinculados junto a esa fila.
- **Obtenido:** a simple vista no aparece nada (solo cambia el texto del botón a "Ocultar vínculos").
- **Reproducible:** siempre
- **Evidencia:** la API sí responde bien: `GET /api/v1/guardians/<id>/link-student/` → 200 con los estudiantes, tanto para pagos.demo como para dir.demo.
- **Viewport:** escritorio
- **Hipótesis de causa:** el panel de vínculos se dibuja **debajo de toda la tabla** (`frontend/src/features/estudiantes/components/EncargadosPage.vue:173`), no junto a la fila. Con los 30 encargados de `seed_masivo` queda fuera de pantalla. Además, `verVinculos` (línea 108) no tiene `catch`: si la llamada falla, no se muestra ningún error.

---

### D-005 · La bandeja de "Documentos emitidos" no muestra nada

- **Caso del plan:** `DOC-03`
- **Tipo:** bug
- **Severidad:** Media
- **Rol con el que ocurrió:** dir.demo
- **Dónde:** /administrativo → Documentos
- **Referencia:** RF-08, RF-11
- **Pasos para reproducir:**
  1. Emitir una constancia de solvencia.
  2. Ir a Documentos → Bandeja de documentos.
- **Esperado:** aparece el documento emitido, con el botón "Volver a descargar".
- **Obtenido:** la bandeja sale vacía, con un mensaje en rojo de que no hay documentos emitidos, aunque sí hay uno.
- **Reproducible:** siempre
- **Evidencia:** en la base hay 1 documento (constancia de solvencia, código `297F15ADE25E`, emitida por pagos.demo). `GET /api/v1/documents/` devuelve `count: 1` tanto para pagos.demo como para dir.demo, así que el problema está en la pantalla. <opcional: captura y consola F12>
- **Viewport:** escritorio
- **Hipótesis de causa:** `DocumentosPage.vue:50` carga documentos, inscripciones y estudiantes con un solo `Promise.all`; si cualquiera de las tres falla, no se muestra nada de la bandeja. Sin confirmar.

---

### D-006 · El monto de un pago no tiene límite máximo

- **Caso del plan:** `PAG-02`
- **Tipo:** falta-funcionalidad
- **Severidad:** Mejora
- **Rol con el que ocurrió:** pagos.demo
- **Dónde:** /administrativo → Pagos → Registrar pago
- **Referencia:** no documentado
- **Pasos para reproducir:**
  1. Registrar un pago con un monto muy alto.
- **Esperado:** advertencia o tope razonable para la mensualidad.
- **Obtenido:** se acepta cualquier monto (solo se rechazan 0 y negativos; el campo admite hasta Q999,999.99).
- **Reproducible:** siempre
- **Evidencia:** `Payment.amount` = `DecimalField(max_digits=8)` con mínimo 0.01 y sin máximo (`backend/apps/payments/models.py:23`).
- **Viewport:** escritorio
- **Hipótesis de causa:** el PROMPT_MAESTRO no fija un monto de mensualidad; es decisión del equipo.

---

### D-008 · Aprobar una solicitud de cambio de nota es muy lento

- **Caso del plan:** fuera de set (Set C, modificaciones de nota)
- **Tipo:** rendimiento
- **Severidad:** Media
- **Rol con el que ocurrió:** dir.demo
- **Dónde:** /administrativo/notas/modificaciones
- **Referencia:** RF-23, RN-05
- **Pasos para reproducir:**
  1. Abrir las solicitudes de cambio de nota.
  2. Aprobar una.
- **Esperado:** cambia a "Aprobada" en 1–2 s.
- **Obtenido:** tarda alrededor de **1 minuto** en cambiar a "Aprobada".
- **Reproducible:** siempre
- **Evidencia:** medido a mano, ~1 min. <opcional: tiempo de la petición en la pestaña Network>
- **Viewport:** escritorio

---

### D-009 · Los datos de salud solo se pueden agregar después de inscribir

- **Caso del plan:** fuera de set (Set B, estudiantes)
- **Tipo:** ux
- **Severidad:** Mejora
- **Rol con el que ocurrió:** dir.demo
- **Dónde:** inscripción de estudiante
- **Referencia:** RF-03
- **Pasos para reproducir:**
  1. Inscribir un estudiante nuevo.
- **Esperado:** poder llenar los datos de salud en el mismo formulario.
- **Obtenido:** hay que inscribir primero y después editar para agregarlos.
- **Reproducible:** siempre
- **Viewport:** escritorio

---

### D-010 · Asistencia: el campo de hora no deja escribir y marca "Presente" solo

- **Caso del plan:** fuera de set (Set B, asistencia)
- **Tipo:** bug
- **Severidad:** Media
- **Rol con el que ocurrió:** guia.demo
- **Dónde:** /operativo → Asistencia (pasar lista)
- **Referencia:** RF-16, RN-11/RN-12
- **Pasos para reproducir:**
  1. Pasar lista.
  2. Intentar escribir una hora en el campo de hora de un estudiante.
- **Esperado:** se puede escribir la hora y queda claro para qué sirve (p. ej. hora de llegada si llegó tarde).
- **Obtenido:** no deja escribir la hora y el estudiante queda marcado como "Presente" automáticamente. No se entiende para qué sirve la hora.
- **Reproducible:** siempre
- **Viewport:** escritorio

---

### D-011 · Diseñar unidad acepta fechas de entrega en el pasado

- **Caso del plan:** fuera de set (Set C, diseño de la unidad)
- **Tipo:** bug
- **Severidad:** Media
- **Rol con el que ocurrió:** dir.demo
- **Dónde:** /operativo → Notas → Diseñar unidad
- **Referencia:** RF-17 (no documentado si se permiten fechas pasadas)
- **Pasos para reproducir:**
  1. Crear una actividad con fecha de entrega anterior a hoy.
- **Esperado:** se rechaza, o al menos se advierte.
- **Obtenido:** se guarda sin aviso.
- **Reproducible:** siempre
- **Viewport:** escritorio

---

### D-012 · Calendario: un evento puede terminar antes de empezar

- **Caso del plan:** fuera de set (Set B, calendario)
- **Tipo:** bug
- **Severidad:** Media
- **Rol con el que ocurrió:** dir.demo
- **Dónde:** Calendario → publicar evento
- **Referencia:** RF-22
- **Pasos para reproducir:**
  1. Crear un evento con hora de fin anterior a la de inicio.
- **Esperado:** error de validación.
- **Obtenido:** se publica.
- **Reproducible:** siempre
- **Viewport:** escritorio

---

### D-013 · Reportes institucionales aceptan fechas futuras

- **Caso del plan:** fuera de set (Set A, reportes)
- **Tipo:** ux
- **Severidad:** Baja
- **Rol con el que ocurrió:** dir.demo
- **Dónde:** /administrativo → Reportes
- **Referencia:** RF-15
- **Pasos para reproducir:**
  1. Generar un reporte con un rango de fechas en el futuro.
- **Esperado:** no se permite, o se advierte que no hay datos.
- **Obtenido:** se genera.
- **Reproducible:** siempre
- **Viewport:** escritorio

---

### D-014 · No hay forma de corregir ni anular un pago

- **Caso del plan:** `PAG-05`
- **Tipo:** falta-funcionalidad
- **Severidad:** Media
- **Rol con el que ocurrió:** pagos.demo
- **Dónde:** /administrativo → Pagos
- **Referencia:** RF-07, RNF-06 (bitácora). El PROMPT_MAESTRO no menciona "anular" explícitamente; decisión del equipo.
- **Pasos para reproducir:**
  1. Registrar un pago con un dato equivocado (monto, mes o recibo).
  2. Buscar cómo corregirlo o anularlo.
- **Esperado:** poder corregir o anular el pago, que quede en la bitácora y que se recalcule la solvencia.
- **Obtenido:** no existe la opción. Un pago mal registrado se queda así para siempre.
- **Reproducible:** siempre
- **Evidencia:** `PaymentViewSet` (`backend/apps/payments/api/views.py:45`) solo tiene crear, listar y ver detalle: no hay editar ni dar de baja.
- **Viewport:** escritorio

---

### D-015 · La pantalla de pagos no tiene filtros

- **Caso del plan:** `PAG-08`
- **Tipo:** ux
- **Severidad:** Mejora
- **Rol con el que ocurrió:** pagos.demo
- **Dónde:** /administrativo → Pagos
- **Referencia:** no documentado
- **Pasos para reproducir:**
  1. Abrir Pagos con los datos de `seed_masivo` (60 estudiantes, 355 pagos).
- **Esperado:** filtros útiles (por sección, por mes, solventes/insolventes).
- **Obtenido:** solo se puede seleccionar un estudiante a la vez.
- **Reproducible:** siempre
- **Viewport:** escritorio

---

### D-016 · No hay opción para dar de baja a un estudiante

- **Caso del plan:** `DOC-07`
- **Tipo:** falta-funcionalidad
- **Severidad:** Media
- **Rol con el que ocurrió:** dir.demo
- **Dónde:** /administrativo → Estudiantes
- **Referencia:** RF-03 (baja lógica, `is_active=False`)
- **Pasos para reproducir:**
  1. Abrir Estudiantes y buscar cómo dar de baja o retirar a un estudiante.
- **Esperado:** una opción de baja o retiro (baja lógica, sin borrar).
- **Obtenido:** no existe en la pantalla, así que DOC-07 (documento para un estudiante retirado) no se pudo probar.
- **Reproducible:** siempre
- **Evidencia:** el backend sí lo permite (`StudentViewSet` es un `ModelViewSet`, `backend/apps/students/api/views.py:43`), pero en `frontend/src/features/estudiantes` no hay ningún botón de baja, retiro ni desactivar.
- **Viewport:** escritorio

---

## Cobertura de mi set

✅ pasó · ❌ falló (ver hallazgo) · ⏭️ no se pudo probar (por qué)

| Caso | Estado | Hallazgo(s) |
|---|---|---|
| PAG-01 | ✅ | |
| PAG-02 | ❌ | D-006 |
| PAG-03 | ✅ | |
| PAG-04 | ✅ | |
| PAG-05 | ❌ | D-014 |
| PAG-06 | ✅ coord/admin no pueden modificar pagos | |
| PAG-07 | ✅ | |
| PAG-08 | ❌ | D-015 |
| DOC-01 | ✅ (se emitió constancia de solvencia) | |
| DOC-02 | ✅ | |
| DOC-03 | ❌ | D-005 |
| DOC-04 | ❌ la bandeja no carga ningún documento con pagos.demo | D-005 (misma causa probable) |
| DOC-05 | ⏭️ el QR apunta a `localhost`, el celular no lo abre (ver "cosas raras") | |
| DOC-06 | ✅ tildes bien en los PDF | |
| DOC-07 | ⏭️ no se pudo: no hay forma de dar de baja | D-016 |
| AVI-01 a AVI-04 | ✅ | |
| CON-01 a CON-05 | ✅ | |
| BUZ-01 | ✅ coord.demo y pagos.demo no tienen opción de buzón (correcto) | |
| BUZ-04 | ❌ | D-001, D-002 |
| BUZ-07 | ❌ | D-003 |
| POR-01 | ❌ | D-003 |
| POR-07 | ✅ (ver "cosas raras") | |
| POR-10 | ❌ | D-001, D-002, D-003 |
| POR-14 / TRV-01 (vista celular) | ✅ se ve bien en celular | |
| POR-02 | ✅ | |
| POR-03 | ⚠️ ver "cosas raras" | |
| POR-05 | ✅ las ausencias se ven | |
| POR-06 | ✅ se ve solvente | |
| POR-08 / POR-09 | ✅ sin registros, la pantalla sale limpia | |
| POR-01 (cambio de estudiante) | ✅ cambia con el selector | |
| POR-15 | ✅ | |
| POR-11, POR-12, POR-13 | ⏭️ no probados | |

## Cosas que me parecieron raras pero no estoy seguro de que sean error

- **El boletín de la familia solo se descarga en la Unidad 1, aunque hay notas hasta la Unidad 3.** Probablemente es correcto: `seed_masivo` solo **publica** boletines de la Unidad 1 (47 publicados, 13 bloqueados por solvencia o plazo), y por RF-34/RN-09/RN-10 la familia solo ve boletines publicados. Las Unidades 2 y 3 tienen notas, pero sus boletines siguen en borrador o aprobados. Para confirmarlo: publicar el boletín de la Unidad 2 con dir.demo en /administrativo/boletines y ver si aparece en el portal. Sí revisaría que el portal explique **por qué** no está disponible (POR-07: "mensaje claro de por qué no").
- **Pagar enero "dos veces" (antes era D-007, descartado).** No era un duplicado: la estudiante (ES034, Renata Choc Reyes) no tenía ningún pago, así que enero estaba pendiente y se guardó bien (recibo `565432`). La base además impide pagar dos veces el mismo mes (`pago_unico_por_mes`). Lo único que revisaría: la pantalla mostraba la insolvencia "desde febrero", y si enero tampoco estaba pagado, debería decir "desde enero". Volver a mirarlo con otro estudiante sin pagos.
- **POR-03, las notas en el portal se ven "con todo el historial".** La familia ve la nota de **cada actividad** (examen, tareas…), no solo la final de la unidad. Revisé la API: `/api/v1/grades/` devuelve `current_score` por actividad y **no** trae `raw_score` ni el historial de modificaciones, así que RN-06 ("sin el historial de modificaciones") técnicamente se cumple. Duda para el equipo: ¿la familia debe ver el detalle por actividad o solo el total por curso y unidad? Además, la respuesta incluye `recorded_by` (el usuario del docente, p. ej. `guia.demo`), que a la familia no le sirve.
- **DOC-05, el QR lleva a `localhost`.** En desarrollo es lo esperado: el celular no puede abrir `localhost` de la compu. Confirmar que en producción el QR use la dirección pública real (configuración, no código).
- **DOC-06, la carta membretada no incluye el nombre del estudiante** a menos que se escriba en el texto libre. En las constancias el nombre con tildes sale bien.
