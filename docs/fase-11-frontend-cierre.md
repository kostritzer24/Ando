# Fase 11 (backend + frontend) — Comunicación del lado del centro: cierre

Octava fase del bloque de frontend, y la segunda (después de la Fase 10) que necesitó construir backend real antes de poder construir la pantalla: `apps/communication` no tenía modelos, serializers, vistas ni URLs — solo el esqueleto de la app. Cubre RF-13, RF-24, RF-25, RNF-10, RN-16, y cierra los RF-35 a RF-37 del portal público que la Fase 10 había dejado pendientes por esta misma razón.

## Backend — `apps.communication` desde cero

- **Modelos** (`docs/modelo-datos.md`, sección `communication`, y [ADR-0006](adr/0006-formato-reporte-conducta.md) para `ConductReport`): `Announcement` (destinatario `todos`/`seccion`, con `expires_at` para HU-36), `ConductReport` con las columnas ampliadas del formato real del centro (gravedad, hechos, medidas, sanción, compromisos, firmas de maestro guía y de dirección) más `ConductReportArticle` como tabla de unión con el catálogo `catalog.ConductRuleArticle`, y `Message` (hilo de buzón enlazado por `original_message`, nunca un objeto de conversación aparte, como pide la sección 8 del prompt maestro).
- **RF-13/HU-36 (`communication/services/announcement.py`):** un aviso es para todos o para una sección, nunca las dos cosas — `avisos_vigentes()` filtra los vencidos sin borrarlos. Solo Dirección publica/edita/retira; el resto de los roles con acceso al área ven los avisos "todos" más los de las secciones a las que están conectados (por asignación docente, o por inscripción de un hijo).
- **RF-24/RF-35 (`communication/services/conduct_report.py`):** `guide_teacher` es siempre el maestro guía real de la sección de la inscripción (`Section.homeroom_teacher`), no necesariamente quien llena el formulario — un maestro guía solo puede registrar reportes de su propia sección; Dirección puede de cualquiera, y queda como `direction_member`. El PDF (`GET /conduct-reports/{id}/download/`) reproduce el formato de `docs/reporte.docx` con las líneas de firma en blanco (RN-15) — cuatro firmas: maestro guía, miembro de dirección, estudiante, encargado.
- **RN-16/RNF-10 (`communication/domain/buzon.py`, `communication/services/buzon.py`):** un mensaje con lenguaje inapropiado (lista curada, comparación por palabra completa sin acentos ni mayúsculas) **nunca se crea** — se rechaza con 400, y quien lo envió queda bloqueado 24 horas reusando `User.locked_until`, el mismo campo del límite de intentos de inicio de sesión (sección 14.1). Una respuesta siempre cuelga del mensaje raíz del hilo, nunca de la última respuesta, y lo deja en estado `respondido`; consultar el hilo (cualquier rol que no sea la familia) lo marca `leído` — sin exponerle ese estado a quien lo envió (HU-25/HU-37: "ni indicador de visto").
- **Nuevo endpoint por rol, no nuevo modelo:** `catalog.ConductRuleArticleViewSet` gana la misma excepción que `ActivityTypeViewSet`/`JustificationTypeViewSet` (Fases 4/7) — leer el catálogo pasa por el área "reportes_conducta" en vez de "datos_maestros", porque el maestro guía necesita marcar artículos sin administrar el catálogo completo.
- **Bug real corregido (no de esta fase):** los endpoints de creación con id interno vs. `public_id` — `ConductReportArticle.article_id` y la validación de sección propia de la familia en `MessageViewSet.create` comparaban un `public_id` (UUID) contra una clave primaria entera, encontrado por las pruebas de la fase (`OverflowError` de SQLite en el primer caso, un 403 siempre en el segundo).
- **`seed_fase3` ya traía los permisos correctos** ("avisos", "reportes_conducta", "buzon" en la matriz de los 8 roles) desde la Fase 3 — no hizo falta tocar la siembra de roles, solo usarlos.
- **`seed_demo` extendida — vacío real encontrado:** `guia.demo` era maestro guía de "Primero básico A" pero nunca tenía ninguna `TeacherAssignment` propia — sin eso no llegaba ni a la lista de sus propios estudiantes (ese alcance siempre se filtra por asignación docente, nunca por `homeroom_teacher`), así que no podía registrar un reporte de conducta de su propia sección. Se le agregó una asignación (Comunicación y lenguaje L1, su sección).

**Verificación real (backend):** 326 pruebas (28 nuevas), 100 % de cobertura en `domain/` y `services/` de `communication`.

## Frontend

- **`frontend/src/features/comunicacion/`** — pantallas compartidas entre el portal administrativo (Dirección) y el operativo (maestro guía), mismo patrón que `CalendarioPage.vue` desde la Fase 8:
  - **`AvisosPage.vue`:** Dirección publica (título, contenido, destinatario, vencimiento opcional) y retira; el resto solo ve, ya filtrado por el backend.
  - **`ReportesConductaPage.vue`:** formulario completo del formato real (checklist de artículos del catálogo, sanción, compromisos) y bandeja con "Descargar PDF".
  - **`BuzonPage.vue`:** bandeja de hilos con estado (`Nuevo`/`Leído`/`Respondido`), expandir para ver el mensaje y responder.
- **Portal público (`frontend/src/features/portal/`):**
  - **`AvisosPage.vue`** (RF-36/RF-37, quinta pestaña del `BottomTabBar` — la que ya anticipaba el mockup de la Propuesta B desde la Fase 3): cartelera arriba, buzón abajo en la misma pantalla (componer mensaje nuevo, ver hilos propios con las respuestas).
  - **`AsistenciaPage.vue`** ampliada con una segunda sección, "Reportes de conducta" (RF-35) — no le tocaba una pestaña propia en el mockup de 5 pestañas, y temáticamente es más cercana a asistencia/comportamiento que a notas o pagos.
- **Navegación:** Avisos se agrega a los tres portales (Dirección y toda la planta operativa tienen `V` según la matriz); Reportes de conducta y Buzón solo para Dirección (administrativo) y el maestro guía (operativo, es el único rol operativo con `E` en esas dos áreas — Docente/Tallerista no).

## Verificación real (frontend)

`vue-tsc --noEmit`, `eslint` y `vitest run` (34 pruebas) sin errores.

3 pruebas de extremo a punta contra un navegador real (Chromium), con el backend vivo y datos de `seed_demo`: Dirección publica un aviso para todos y dos dirigidos a secciones distintas, y docente.demo (asignado a Segundo básico) ve el suyo y el de "todos" pero no el de la otra sección; el maestro guía registra un reporte de conducta completo con un artículo marcado y descarga el PDF real; la familia escribe al buzón, el maestro guía responde desde su bandeja, la familia ve la respuesta y el reporte de conducta de ese mismo hijo en su portal, y por último un mensaje con lenguaje inapropiado se rechaza con el aviso correspondiente (RN-16).

**Bug real de frontend encontrado y corregido (no de esta fase, de la Fase 8):** `HorarioGridPage.vue` reseteaba el docente elegido al primero de la lista cada vez que recargaba los datos — incluida la recarga automática después de guardar un bloque de horario. Con solo dos docentes en la siembra (`docente.demo` antes que `tallerista.demo`) el primero de la lista siempre coincidía con quien se estaba editando, así que el bug quedaba invisible; agregar la asignación de `guia.demo` cambió el orden y la selección saltaba de docente a mitad de la prueba, sin aviso. Se corrigió para no resetear la selección si la persona elegida sigue teniendo asignaciones — un caso real de "cambiar de docente sin darse cuenta" que hubiera podido pasar en producción con Dirección editando el horario de una persona.

## Siguiente

Con esto se cierra la comunicación del lado del centro. Queda pendiente en el portal público solo RF-30 (puntos para aprobar, "debería tener", sin backend) — ver `docs/pendiente-frontend.md`. Según el plan maestro, después sigue la Fase 12 (reportes institucionales, RF-15).
