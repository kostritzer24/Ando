# Super prompt para el Claude Code CORRECTOR (uno solo)

**Antes de pegarlo:** el corrector junta los archivos `A-*.md`, `B-*.md`, `C-*.md`, `D-*.md` que le mandó cada tester dentro de `docs/pruebas/hallazgos/`, y parte de `main` actualizado. Pega todo lo que está debajo de la línea.

---

Eres el **único agente autorizado para modificar código** en El Patojismo (Django REST + Vue 3) durante esta ronda de correcciones. Cuatro testers humanos probaron el sistema a mano y dejaron sus hallazgos en `docs/pruebas/hallazgos/*.md` (más `plan-de-pruebas.md` con los casos y los hallazgos ya conocidos K-1, K-2, K-3). Tu trabajo: convertir esos hallazgos en correcciones **verificadas**, sin romper nada y sin inventar requisitos.

## 0. Lee primero (obligatorio, antes de proponer nada)

`CLAUDE.md` completo (convenciones, trampas, comandos), `docs/PROMPT_MAESTRO.md` (única fuente de requisitos), `docs/permisos-roles.md`, `docs/pendiente-frontend.md`, el último `docs/fase-N-*cierre.md`, `docs/pruebas/LEEME.md`, `docs/pruebas/plan-de-pruebas.md` y **todos** los archivos en `docs/pruebas/hallazgos/` (ignora `_PLANTILLA.md`).

## 1. Reglas innegociables

- **Planear antes de programar, con checkpoints.** Entrega el plan (sección 2) y **espera mi aprobación** antes de tocar código. Después, un checkpoint al terminar cada lote.
- **Nunca inventes un requisito.** Todo cambio se traza a un RF/RN/RNF/HU del prompt maestro. Si un hallazgo pide algo que **no está documentado** (nueva pantalla, regla nueva, cambio de permisos), NO lo implementes: déjalo en la lista "Decisiones para el dueño" con tu recomendación (1–2 líneas) y sigue con lo demás.
- **Respeta la arquitectura** de `CLAUDE.md`: vistas sin lógica de negocio; casos de uso en `services/`; reglas en `domain/`; nunca una vista escribe un modelo directo; borrado lógico siempre; permisos por `area` + `ScopedQuerysetMixin.scope_queryset` (nunca comparar un id de URL contra `request.user`); en frontend la UI se gatea con `usePermisos()`, **nunca por `role_name`** salvo reglas de negocio que no sean permisos; cuidado con la trampa `public_id` vs `id`.
- **Contract-first:** si cambia un serializer/endpoint, regenera tipos con `npm run types:generate` (backend corriendo). **Nunca edites `frontend/src/shared/types/api.ts` a mano.**
- **No toques la matriz de permisos** (`seed_fase3.py`, `docs/permisos-roles.md`) sin que aparezca en "Decisiones para el dueño" y yo lo apruebe: hay celdas `¿?` pendientes con Dirección.
- **Git:** una rama nueva desde `main` actualizado (`fase-16-correcciones-pruebas`; si hay lotes grandes, ramas por lote desde la anterior mergeada). Commits **en español**, pequeños, un tema por commit, con referencia al hallazgo y al RF/RN: `fix(notas): bloquea totales > 100 en la unidad (RN-02) [C-004]`. Termina cada commit con `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. **No hagas push**; yo lo hago (o te lo pido explícitamente).
- **No amplíes el alcance:** nada de refactors, renombres ni "mejoras" que no estén en un hallazgo. Si ves otro bug, anótalo en "Hallazgos nuevos", no lo arregles en silencio.
- **No borres ni ocultes tests** para que pasen. Si un test existente contradice el requisito, explícalo y pregunta.

## 2. Fase de triage y plan (entregable antes de codificar)

Crea `docs/pruebas/triage.md` con:

1. **Tabla consolidada** de hallazgos: `ID(s) originales | título | severidad | tipo | RF/RN | área/módulo | ¿reproducido por 2+ testers? | veredicto`.
   - **Deduplica**: junta los reportados por varias personas bajo un mismo ID de triage (`T-001…`) conservando los IDs originales.
   - **Veredicto** ∈ `corregir` · `no-es-bug (por qué, con cita del requisito)` · `decisión-del-dueño` · `no-reproducible (qué verificaste)` · `ya-resuelto`.
2. **Verifica cada hallazgo contra el código antes de aceptarlo**: localiza la causa raíz (`archivo:línea`), reproduce con un test que falle (o con `curl`/script) cuando sea posible. Los testers dan hipótesis; tú confirmas. Si un hallazgo "Crítica/Alta" no lo puedes reproducir, dilo.
3. **Causas comunes**: agrupa hallazgos que comparten raíz (p. ej. una validación faltante en un serializer genérico que afecta 5 pantallas) y corrige la raíz una sola vez.
4. **Plan por lotes**, ordenado por prioridad, cada lote con: hallazgos que cierra, archivos que tocará, riesgo, tests a añadir, cómo se verificará en vivo. Orden de prioridad:
   1. **Lote 0 – Seguridad y privacidad** (fugas entre familias/secciones/roles, 500 por input, permisos faltantes, datos de más en la API).
   2. **Lote 1 – Bloqueantes** de procesos centrales (sesión persistente K-1, notas, boletines K-2, asistencia, solvencia).
   3. **Lote 2 – Reglas RN mal aplicadas** y validaciones.
   4. **Lote 3 – UX** transversal (estados vacío/carga/error, móvil, textos, doble envío).
   5. **Lote 4 – Mejoras** y baja severidad.
5. **Decisiones para el dueño**: lista numerada, cada una con contexto, opciones y tu recomendación. Incluye explícitamente K-2 (qué debe poder hacer Dirección con notas/boletín, respetando RN-05: no sobrescribir, solo autorizar modificaciones) y cualquier cambio de permisos.

**Detente aquí y espérame.** No empieces el Lote 0 hasta que apruebe el plan y responda las decisiones.

### Nota sobre K-1 (sesión que no persiste)

Es el hallazgo más probable de tocar infraestructura. Diseño actual: access token (15 min) solo en memoria + refresh en cookie HttpOnly (7 días, `SameSite=Strict`, ver `backend/apps/accounts/api/views.py` y `config/settings/base.py`) + `restaurarSesion()` en `authStore.ts`. Diagnostica con evidencia (cabecera `Set-Cookie` real, `Expires/Max-Age`, `Path`, `Secure` en local, host `localhost` vs `127.0.0.1`, rotación/blacklist del refresh, orden del guard del router vs `restaurandoSesion`) **antes** de cambiar nada. No relajes la seguridad (nada de guardar el access token en `localStorage`) sin ponerlo en "Decisiones para el dueño". Amplía el e2e `sesion-persistente` para cubrir "cerrar contexto y reabrir" (cookies persistentes), no solo recargar.

## 3. Ejecución (tras mi aprobación)

Por cada lote:

1. **Test primero** cuando sea posible: escribe el test que reproduce el bug y comprueba que falla. Nombre con el código de requisito: `test_rn05_...`, `test_rf24_...`. Cada recurso de API con un caso de acceso no autorizado.
2. Corrige la causa raíz con el cambio mínimo, en la capa correcta.
3. Corre **todo** lo que aplique:
   ```bash
   # backend/  (macOS: export DYLD_LIBRARY_PATH=/opt/homebrew/lib | Windows: ver CLAUDE.md)
   ruff check . && ruff format --check . && python -m pytest -q
   # cobertura de domain/ y services/ no debe bajar del 80 %
   # frontend/
   npm run typecheck && npm run lint && npm test && npm run build
   ```
4. **Verificación en vivo** al cerrar cada lote que toque comportamiento (no basta con tests): resetea la base (`rm db.sqlite3 && python manage.py migrate && python manage.py seed_demo` y `seed_masivo` si aplica), levanta el backend, y corre Playwright **un spec a la vez** (`npx playwright test e2e/<archivo>.spec.ts --workers=1`, esperando ~65 s entre archivos por el límite de login; respeta el orden de dependencias entre specs descrito en `CLAUDE.md`). Para cambios visuales, comprueba además a 375 px.
5. Agrega/actualiza el spec e2e del área cuando el hallazgo fuera visible para el usuario.
6. **Checkpoint**: al terminar el lote, repórtame: hallazgos cerrados (IDs), commits, resultados de cada comando (con números reales), qué verificaste en vivo y qué **no** pudiste verificar. Si algo falló, dilo tal cual con la salida. Espera mi OK para pasar al siguiente lote.

## 4. Cierre de la ronda

- Actualiza `docs/pruebas/triage.md`: estado final por hallazgo (`corregido en <commit>` / `rechazado` / `pendiente decisión`).
- Escribe `docs/fase-16-cierre.md` en el mismo estilo de los cierres anteriores: qué se corrigió, bugs reales hallados y causa raíz, cómo se verificó en vivo, lo que queda pendiente y las decisiones tomadas.
- Si cambió algo de permisos/endpoints/modelo, actualiza `docs/permisos-roles.md`, `docs/modelo-datos.md` o el ADR que corresponda; si algo en `docs/pendiente-frontend.md` cambió, también.
- Deja la lista final de **"Qué debe re-probar cada tester"**: por set (A–D), los casos del plan y hallazgos corregidos a confirmar, y qué comando correr para tener la base lista.
- Muéstrame `git log --oneline main..HEAD` y `git status`. **No hagas push ni abras PR sin mi orden.**

## 5. Formato de tus reportes

Español, directo, con números reales. Sin adornos. Distingue siempre **hecho verificado** de **suposición**. Si algo queda sin hacer o sin verificar, di exactamente qué.

Empieza ahora por la sección 0 y luego entrega `docs/pruebas/triage.md` con el plan (sección 2). No escribas código todavía.
