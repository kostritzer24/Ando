# ADR-0007: Bibliotecas fundacionales para autenticación, esquema de API, CORS y seguridad de cabeceras

**Fecha:** 2026-09-20 (confirmado 2026-09-20)
**Estado:** Aceptado — `djangorestframework-simplejwt`, `drf-spectacular` y `django-cors-headers` confirmados

## Contexto

La sección 13 del prompt maestro fija el stack en términos generales (Django 5.x, DRF, "autenticación por token JWT", Vue 3, Vite, Vue Router, Pinia, Axios, pytest, Ruff, Vitest, Playwright, pre-commit, GitHub Actions) pero no nombra las bibliotecas concretas para JWT, para generar el esquema OpenAPI, para CORS ni para cabeceras de seguridad — piezas que la Fase 3 necesita desde el primer commit. Van aquí, separadas de ADR-0005 (que cubre PDF/QR/plantillas, necesarias más adelante), porque estas sí bloquean el arranque de la Fase 3.

## JWT con rotación de token de refresco

| Opción | A favor | En contra |
|---|---|---|
| **`djangorestframework-simplejwt`** (recomendada) | Es la biblioteca de facto para JWT en DRF; soporta rotación de refresh token y lista de revocación (`token_blacklist`) de fábrica, que es exactamente lo que pide la sección 14.1. | Ninguna relevante para este alcance. |
| Django sesiones + DRF TokenAuthentication | Ya viene con Django, cero dependencias nuevas. | No es JWT (la sección 13 lo pide explícitamente) y no dan vida corta ni rotación sin construirlo a mano. |

**Recomendación:** `djangorestframework-simplejwt`, con el token de acceso en memoria del frontend (nunca en `localStorage`, para reducir superficie de XSS) y el token de refresco en cookie `HttpOnly/Secure/SameSite=Strict` servida por una vista propia, no por el flujo por defecto del paquete (que expone el refresh token en el cuerpo de la respuesta).

## Esquema OpenAPI

| Opción | A favor | En contra |
|---|---|---|
| **`drf-spectacular`** (recomendada) | Activamente mantenido, genera OpenAPI 3 directo desde las vistas y serializers de DRF sin decorar cada endpoint a mano; de ahí se derivan los tipos de TypeScript del frontend (sección 12.3). | Ninguna relevante para este alcance. |
| `drf-yasg` | Más antiguo, generación de OpenAPI 2 (Swagger) por defecto. | Menos alineado con OpenAPI 3 y con menor mantenimiento activo. |

**Recomendación:** `drf-spectacular`.

## CORS

| Opción | A favor | En contra |
|---|---|---|
| **`django-cors-headers`** (recomendada) | Estándar de facto, permite restringir orígenes explícitamente (sección 14.4: "CORS restringido a los dominios del proyecto, sin comodines"). | Ninguna relevante para este alcance. |

No hay alternativa razonable con menos peso para este problema puntual.

## Límite de tasa (rate limiting)

**No se agrega ninguna biblioteca nueva.** DRF trae throttling nativo (`AnonRateThrottle`, `UserRateThrottle`, y clases de throttling personalizadas por vista), suficiente para "límite de tasa por endpoint sensible" (sección 14.4) y para el límite de la página de verificación por QR (RF-14). Agregar una biblioteca externa para esto iría en contra de la regla de trabajo 8.

## Cabeceras de seguridad y CSP

| Opción | A favor | En contra |
|---|---|---|
| **Configuración nativa de Django** (`SECURE_*`, `django.middleware.security.SecurityMiddleware`, `X_FRAME_OPTIONS`) + una política CSP escrita a mano en un middleware propio de `core/` (recomendada) | Django ya cubre HSTS, cookies seguras, `X-Content-Type-Options` sin dependencias nuevas; una CSP para un sitio con un solo origen de API y un solo frontend es corta y no justifica una biblioteca. | Hay que mantenerla a mano si la política crece. |
| `django-csp` | Sintaxis declarativa para políticas CSP complejas. | Es una dependencia más para una política que en este proyecto es simple y estable (un origen de frontend, Google Fonts si se usan, nada más) — no se justifica todavía. |

**Recomendación:** configuración nativa, sin `django-csp` por ahora. Se reconsidera en un ADR nuevo si la política CSP crece lo suficiente para justificarlo.

## Decisión

Confirmado por el equipo. Se instalan en `backend/requirements/base.txt` al construir la Fase 3.

## Consecuencias

- Si se aprueba, `requirements/base.txt` de la Fase 3 incluye `djangorestframework-simplejwt`, `drf-spectacular`, `django-cors-headers`.
- El resto (JWT blacklist, throttling, cabeceras) se configura con lo que ya trae Django/DRF, sin dependencias adicionales.
