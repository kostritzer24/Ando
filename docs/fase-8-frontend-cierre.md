# Fase 8 (frontend) — Horarios y calendario: cierre

Quinta fase del bloque de frontend. Cubre RF-06, RF-22, RF-26: grilla de horario del centro, horario propio de solo lectura y calendario institucional/personal.

## Qué se construyó

- **`HorarioGridPage.vue`** (RF-06/HU-06, portal administrativo, Dirección): elegir un docente o tallerista y ver su semana completa en una grilla de 6 períodos × 5 días (RN-13). Cada celda vacía tiene un botón "+" que abre un formulario para elegir cuál de las asignaciones existentes de esa persona va ahí — el formulario nunca ofrece crear una asignación nueva, solo las que ya existen (eso sigue siendo de Fase 5).
- **Decisión de diseño sobre el cruce de horario (RN-13/HU-06):** el pendiente original pedía "resaltar en la grilla la celda donde ese docente ya tiene clase" cuando `POST /schedule-blocks/` devuelve el error de cruce. En vez de eso, la grilla solo ofrece el botón "+" en las celdas que ya se ven vacías para esa persona, revisando todas sus asignaciones a la vez (no solo la que se está por elegir) — así el cruce queda evitado por construcción en el camino normal, en vez de dejarlo ocurrir y solo explicarlo después. Como red de seguridad para el caso raro de una carrera entre dos sesiones de Dirección editando al mismo tiempo, si el backend igual rechaza la creación, el frontend recarga la grilla (que entonces ya muestra la celda ocupada de verdad) en vez de tratar de adivinar el mensaje de error.
- **`MiHorarioPage.vue`** (portal operativo, Docente/Docente con sección a cargo/Tallerista): vista de solo lectura de `GET /schedule/mine/`, misma grilla de 6×5 pero sin ninguna acción — Dirección no tiene este enlace (ve el horario completo desde la pantalla administrativa).
- **`CalendarioPage.vue`** (componente compartido entre los dos portales): un docente/guía/tallerista solo puede publicar tipo "asignación docente" (el `<select>` de tipo ni siquiera ofrece "institucional" — el backend la rechaza por RN-17), opcionalmente ligado a una de sus asignaciones; solo puede editar/eliminar lo que publicó. Dirección puede además publicar avisos institucionales y editar o eliminar cualquier evento del calendario, propio o ajeno — la única combinación de rol con ese alcance.

## Verificación real

3 pruebas de extremo a punta contra un navegador real (Chromium), con el backend vivo y datos de `seed_demo`: Dirección arma el horario de `docente.demo` y lo quita después; un docente ve su propio horario reflejando lo que Dirección acaba de armar; un docente publica un evento propio y no puede elegir "institucional", Dirección publica un aviso institucional y puede editar el evento del docente, y el docente ve el aviso institucional en su lista pero sin botones de editar/eliminar. `vue-tsc --noEmit`, `eslint` y `vitest run` (34 pruebas) sin errores.

Nota de la prueba en navegador: `window.confirm()` se dismiss automáticamente en Playwright si no se engancha `page.once("dialog", (d) => d.accept())` antes del clic — el mismo patrón ya usado en `catalogo-cursos.spec.ts` para "Dar de baja". La primera corrida de la prueba de "quitar" un bloque de horario falló en silencio por esto (el clic en "Quitar" no borraba nada, la celda seguía ocupada) hasta agregar el enganche del diálogo.

## Siguiente

Fase 9 (frontend) — Pagos, solvencia y documentos: registrar pagos, consultar solvencia y emitir constancias, bandeja de boletines (generar/aprobar/publicar) con los mensajes de RN-09/RN-10 que ya devuelve el backend. Detalle completo en `docs/pendiente-frontend.md`.
