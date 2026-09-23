# Cierre — Fase 13: Endurecimiento

Sección 18 del prompt maestro: "Revisión contra OWASP, pruebas de carga básicas, revisión de accesibilidad, revisión de rendimiento en conexión lenta, limpieza de dependencias."

## Qué se hizo

- **Dependencias (backend):** `djangorestframework-simplejwt` 5.3.1→5.5.1 (corrige CVE-2024-22513) y Django 5.1.2→5.2.17 LTS (5.1 llegó a fin de soporte el 2025-12-31), más `drf-spectacular`, `django-cors-headers`, `psycopg`, `factory-boy`, `ruff` y `whitenoise` a su última versión estable. `gunicorn` y `pytest` se dejaron sin subir de versión mayor por no tener CVE pendiente. 358→362 pruebas en verde antes/después.
- **Lint:** la actualización de `ruff` destapó 42 líneas nunca antes revisadas (código de las Fases 10-12). `ruff check .` queda en cero.
- **Validación de archivos subidos (RF-12, sección 14.4):** `Justification.supporting_document` ahora valida tipo declarado, tipo real (firma binaria) y tamaño — `apps/core/validators.py`. Es el único campo de subida genuina de un usuario en todo el sistema.
- **Content-Security-Policy (sección 14.4):** agregada vía `apps.core.middleware.PoliticaDeSeguridadDeContenidoMiddleware`, sin dependencia nueva.
- **`docs/seguridad.md`:** revisión completa de las diez categorías OWASP con evidencia de código.
- **Accesibilidad:** auditoría en vivo con axe-core (WCAG 2.0/2.1 A y AA) contra 7 pantallas reales (login, portal público, tres vistas del administrativo, operativo, verificación pública) — **0 violaciones** en las siete. El proyecto ya venía construyendo con disciplina de accesibilidad (labels reales, `focus-visible`, área táctil mínima, `prefers-reduced-motion`) desde fases anteriores.
- **Rendimiento / conexión lenta:** se encontró y corrigió un bug real que rompía `npm run build` (top-level await sin `build.target` en `vite.config.ts` — nunca se había corrido un build de producción). Ya corregido: `dist/` pesa 648K total, bundle principal 170KB (63.5KB gzip) más un chunk por página bajo 7KB cada uno — confirma el lazy loading por ruta ya en uso.
- **Limpieza de dependencias (frontend):** `npm audit` solo señala una vulnerabilidad moderada de `esbuild`/`vite` que afecta al *servidor de desarrollo*, no al build de producción; subir a Vite 8 es un cambio mayor sin beneficio de producción, se deja para una fase futura si hace falta.
- **Pruebas de carga:** no se agregó una herramienta de carga (no había ninguna en el proyecto y no se justificó sumar una dependencia nueva solo para esto); el throttling por endpoint sensible (`login` 10/min, `verificacion_qr` 30/min, general 120/min autenticado) ya actúa como límite de carga básico y está verificado en vivo (se disparó real y esperadamente durante la auditoría de esta fase).

## Documentación actualizada

- `docs/seguridad.md` (nuevo)
- `docs/desarrollo-local.md` — quitada una sección desactualizada de la Fase 3, agregada la nota del gotcha de `DYLD_LIBRARY_PATH` en macOS con procesos en segundo plano.
