# Fase 17: comunicación de dos vías y promedio de unidad

Rama: `fase-17-comunicacion-y-promedio`. Sale de `fase-16-correcciones-pruebas`, porque `main` todavía no tiene las fases 15 y 16. El PR contra `main` se abre cuando esas dos estén fusionadas.

Origen: la capacitación con docentes. Dirección encarga a una docente la comunicación con los padres, pero no se crea un rol nuevo, así que los permisos nuevos son para todos los docentes. Además, a veces no da tiempo de completar las actividades de una unidad.

## Requerimientos

Están documentados en `docs/PROMPT_MAESTRO.md`:

- **Revisados:** RF-13, RF-25, RF-37, HU-25 y HU-37.
- **Nuevos:** RF-38 (el centro inicia una conversación), RF-39 (repartir puntos) y RF-40 (promediar la unidad).
- **Reglas nuevas:**
  - RN-18: avisos propios.
  - RN-19: visibilidad de la conversación y "no leído" por persona.
  - RN-20: reparto de puntos.
  - RN-21: sin punteo máximo no se califica.
  - RN-22: unidad promediada.

También se actualizaron `docs/permisos-roles.md` (DOC pasa a `E` en Avisos, notas 10 y 11) y `docs/modelo-datos.md`, y se agregó el ADR-0008 (buzón por conversaciones).

## Qué se hizo

| Cambio | Backend | Frontend |
|---|---|---|
| Avisos (RF-13, RN-18) | Migración `accounts/0004`: Docente pasa a `editar` en avisos. Autoría validada en `communication/domain/announcement.py`. Campos `puede_editar` y `published_by_name`. `GET /announcements/target-sections/` para no abrirle el catálogo al docente. El docente ve también los avisos que publicó | Cartelera con Editar/Retirar solo si `puede_editar`; nombre de quien publicó |
| Buzón (RF-25, RF-37, RF-38, RN-19) | Modelos `Conversation`, `Message` y `ConversationRead`. Migraciones `communication/0004` a `0006`. `/conversations/` con `reply`, `unread-count` y `recipients`. RN-16 aplica a cualquier mensaje | Bandeja ordenada por el último mensaje con «Sin leer»; «Nuevo mensaje» con buscador «Encargado / Alumno»; la familia inicia y responde en el portal; contador en el menú y en la pestaña Avisos |
| Repartir puntos (RF-39, RN-20, RN-21) | `Activity.max_score` admite nulo. `POST /activities/distribute/`, con bitácora. La plantilla y el registro de notas rechazan actividades sin punteo máximo | Punteo máximo opcional, botón «Repartir puntos», «Sin punteo» en la tabla; «Capturar notas» no ofrece actividades sin máximo |
| Promediar (RF-40, RN-22) | Modelo `UnitAveraging` (`grading/0004`). La fórmula vive solo en `calcular_nota_unidad`, que también usan `nota_de_unidad` y `notas_por_curso_y_unidad`. Los consumidores son el boletín, el consolidado, el reporte de notas, el avance del boletín y el nuevo `GET /grades/unit-summary/`. Endpoints `POST /activities/average/` y `GET /activities/unit-status/`. No se toca `raw_score` ni `current_score`. El promedio queda bloqueado si hay un boletín aprobado o publicado | «Promediar unidad», que ofrece dar de baja actividades sin notas; «Quitar promedio»; etiqueta «Promediada sobre N pts» en diseñar y en capturar. El portal ya no suma en el navegador y lee `unit-summary` |
| Calendario | Sin cambios | Verificado en el E2E nuevo |

## Decisiones

- **El promedio se bloquea desde que hay un boletín aprobado, no solo publicado.** Lo decidió el dueño en el plan: aprobar congela `ReportCard.contenido`.
- **La familia solo ve la nota de la unidad.** `unit-summary` no le dice si la unidad está promediada; sigue la decisión de oct. 2026 de que la familia vea solo la nota total.
- **El "no leído" no es un "visto".** Nadie más ve lo que leyó cada persona (HU-25).
- **Migración del buzón:**
  - Cada mensaje raíz pasa a ser una conversación, y las respuestas se cuelgan de ella sin recrearse (conservan `public_id`, fechas y remitentes).
  - Cada remitente queda como lector hasta su último mensaje.
  - Un estado "leído" sin respuesta no dice quién lo leyó, así que queda como no leído.
  - El estudiante de la conversación es el vinculado al encargado que escribió, con inscripción en esa sección.
  - Si un hilo no se puede resolver, la migración se detiene y lista los ids, en lugar de perderlo en silencio.
  - Solo se revierte con el buzón vacío.
- **RF-30 (puntos que faltan para aprobar) sigue pendiente.** Cuando se construya, debe leer `unit-summary` y no recalcular.

## Errores reales encontrados al verificar

- **El bloqueo de RN-16 se perdía.** El rechazo levantaba la excepción dentro de `transaction.atomic` y deshacía también el bloqueo. Ahora el filtro corre fuera de la transacción.
- **Esquema de la API con paginación inexistente.** drf-spectacular declaraba paginados los endpoints de lista nuevos (`recipients`, `unit-summary`, `target-sections`). Se corrigió con `pagination_class=None`.
- **Fórmula duplicada en el portal.** El portal sumaba `current_score` en el navegador; con la unidad promediada habría mostrado otra nota. Ahora usa `unit-summary`.
- **Comportamiento conocido de «Diseñar unidad» y «Capturar notas».** Al cambiar de curso, las pantallas vuelven a elegir la Unidad 1 cuando terminan de cargar. Si la persona eligió otra unidad antes de que termine la carga, se le cambia. El E2E lo sortea; en la pantalla no se cambió.

## Verificación

- **Backend:**
  - `ruff check .` limpio.
  - `pytest`: 586 pruebas pasan.
  - Cobertura de `communication` y `grading` (`domain/` y `services/`): 98 %; ningún archivo baja de 94 %.
  - Pruebas nuevas:
    - `test_rf13_rn18_hu36_avisos.py`
    - `test_rf25_rf37_rf38_rn16_rn19_buzon.py`
    - `test_rf25_rn19_migracion_buzon.py` (`MigrationExecutor`: hilo viejo → conversación)
    - `test_rf13_rn18_migracion_docente_avisos.py`
    - `test_rn20_rn21_rn22_repartir_y_promediar.py` (dominio)
    - `test_rf39_rf40_rn20_rn21_rn22_repartir_y_promediar.py`
  - Casos de acceso no autorizado: un docente edita un aviso ajeno, una familia abre la conversación de otra, un docente promedia o reparte en una asignación ajena, una familia pide las notas de otro estudiante.
- **Frontend:**
  - `npm run types:generate` contra el backend real.
  - `typecheck`, `lint` y `npm test` (69 pruebas) pasan.
- **E2E** (base reseteada, un archivo a la vez, 65 s entre archivos):
  - Pasan, en orden: iniciar-sesion, sesion-persistente, reportes, catalogo-cursos, catalogo-ciclos-secciones, horarios, asistencia, notas, pagos-documentos-boletines, expedientes-asignaciones, pantallas-de-solo-lectura, formularios-y-cuenta-nueva, **comunicacion-y-promedio (nuevo, 3/3)** y usuarios.
  - `portal-publico` pasa en su propia base.
  - `comunicacion` falla en la corrida encadenada: `expedientes-asignaciones` le asigna Tercero básico a `docente.demo`, y desde ahí ese docente ve el aviso de Tercero básico que el spec da por ajeno. En su propia base limpia pasa completo (3/3). Ver la nota de `CLAUDE.md`.
  - `cambio-contrasena` no se corrió: necesita preparar a mano el usuario `cambio.demo`.

## Producción (Neon): pendiente al desplegar

Correr `python manage.py migrate`. Incluye:

1. `accounts/0004_docente_publica_avisos`: el rol Docente ya sembrado pasa a `editar` en avisos.
2. `communication/0004` a `0006`: crea las conversaciones y **migra los mensajes de buzón existentes** (migración de datos 0005). Si se detiene, el mensaje dice qué mensajes no tienen estudiante o encargado resoluble; hay que corregir el vínculo o la inscripción y volver a correrla.
3. `grading/0004_repartir_y_promediar`: `max_score` admite nulo y se crea la tabla de unidades promediadas.

Conviene sacar un respaldo o una rama de Neon antes de migrar: la migración del buzón no se revierte con datos.
