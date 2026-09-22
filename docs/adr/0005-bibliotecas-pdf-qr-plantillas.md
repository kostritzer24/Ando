# ADR-0005: Bibliotecas para PDF, código QR y lectura de plantillas

**Fecha:** 2026-09-20 (confirmado 2026-09-20)
**Estado:** Aceptado — WeasyPrint, `qrcode` y `openpyxl` confirmados por el equipo

## Contexto

El sistema necesita, además de Django/DRF: generar documentos PDF (boletines, constancias, cartas — RF-08, RF-09, RF-11), generar y validar códigos QR (RF-14), y leer/escribir plantillas de calificaciones y asistencia en hoja de cálculo (RF-19 a RF-21). Ninguna de estas tres cosas la resuelve la biblioteca estándar de Python ni Django por sí solos, así que corresponde documentarlas aquí antes de instalarlas, en vez de agregarlas sin más en la Fase 3/6/7/9 cuando se necesiten.

## Opción para generación de PDF

| Opción | A favor | En contra |
|---|---|---|
| **WeasyPrint** (recomendada) | Convierte HTML/CSS a PDF; permite diseñar boletines y constancias como plantillas Django normales, reutilizando el mismo lenguaje de diseño del resto del sistema. Buen soporte de tipografías y disposición para documentos con logo y QR. | Depende de bibliotecas del sistema operativo (Pango, Cairo) que hay que instalar en la imagen de Render. |
| ReportLab | Muy maduro, sin dependencias de sistema. | Se programa por coordenadas y objetos gráficos, no con HTML/CSS — mucho más lento de mantener para alguien que no programó el documento original. |
| xhtml2pdf | Puro Python, fácil de instalar. | Soporte de CSS limitado; los documentos institucionales (RNF-09) necesitan un diseño cuidado que xhtml2pdf no maneja bien. |

**Recomendación:** WeasyPrint, generando los documentos desde plantillas HTML que comparten los tokens de diseño de la Fase 2.

## Opción para códigos QR

| Opción | A favor | En contra |
|---|---|---|
| **`qrcode` + Pillow** (recomendada) | Estándar de facto en Python, genera la imagen que WeasyPrint puede insertar directo en el PDF. | Ninguna relevante para este alcance. |

No hay alternativa razonable con menos peso: es la biblioteca mínima para esta necesidad puntual, conforme a la regla de trabajo 8.

## Opción para lectura y escritura de plantillas

| Opción | A favor | En contra |
|---|---|---|
| **openpyxl** (recomendada) | Lee y escribe `.xlsx` sin ejecutar fórmulas ni macros si se abre con `data_only` y sin `keep_vba`; es la opción más directa para "generar la plantilla" y "leer solo valores" que exige la sección 14.4. | Ninguna relevante para este alcance. |
| pandas + openpyxl | Más cómodo para transformar datos en memoria. | Agrega una dependencia grande (pandas) solo para leer una hoja con una estructura fija — va en contra de la regla de trabajo 8. |

**Recomendación:** openpyxl solo, sin pandas.

## Decisión

Confirmadas por el equipo. `openpyxl` ya está instalada y en uso desde la Fase 6 (`attendance/services/template.py`, RF-21). `weasyprint` y `qrcode` quedaron instaladas y en uso en la Fase 9 (`documents/services/issuance.py`, RF-08/RF-11/RF-14) — versiones `weasyprint==70.0` y `qrcode[pil]==8.2` en `requirements/base.txt`.

**Nota de entorno local (macOS):** WeasyPrint necesita las bibliotecas de sistema de Pango/Cairo/GDK-Pixbuf en el buscador de dylibs. En Homebrew (`brew install pango`) esas rutas no quedan en el buscador por defecto de macOS, así que `backend/.venv/bin/activate` exporta `DYLD_FALLBACK_LIBRARY_PATH` apuntando a `/opt/homebrew/lib` — no aplica en producción, donde Render corre Linux con las dependencias de sistema instaladas directo (ver `docs/despliegue.md`, Fase 14).

## Consecuencias

- Si se aprueba, `requirements/base.txt` incluye `weasyprint`, `qrcode[pil]` y `openpyxl`.
- El paso de construcción en Render para el backend necesita las dependencias de sistema de WeasyPrint (Pango, Cairo, GDK-Pixbuf); esto se documenta en `docs/despliegue.md` en la Fase 14.
- La validación de "no ejecutar fórmulas ni macros" de la plantilla cargada (sección 14.4) se implementa leyendo con `openpyxl` en modo `data_only=True` y rechazando explícitamente cualquier archivo con macros (`.xlsm`).
