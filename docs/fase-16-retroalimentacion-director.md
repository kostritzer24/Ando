# Retroalimentación del director (demostración del 16-oct-2026)

Diez cambios pedidos tras mostrar la versión de Render + Neon. Rama `fase-16-correcciones-pruebas`.

| # | Pedido | Qué se hizo |
| --- | --- | --- |
| 1 | Marcar todos presentes | `POST /attendance/mark-all-present/` (sección o toda la jornada, sin pisar lo ya marcado) y botones en la pantalla de asistencia. |
| 2 | Talleres como clases normales | Se eliminó la plantilla de Excel (descarga/subida), sus rutas, pantalla y pruebas. El tallerista pasa lista diaria; la familia la ve a diario. |
| 3 | Dos horarios | Básicos (receso 10:00–10:40) y bachillerato (10:40–11:20) en `scheduling/domain/day_structure.py`; la jornada sale del grado. El cruce de un docente se mide por hora real, no por número de período. API y PDF de horario muestran la hora que corresponde. |
| 4 | Error al abrir pestañas | Causa inferida (no se revisaron los logs de Render): arranque en frío de Render/Neon. El cliente HTTP reintenta las lecturas (GET) ante 502/503/504 o sin respuesta. |
| 5 | Dirección en documentos | «Casa 85 zona 2 colonia el recuerdo, El Patojismo». |
| 6 | Cierre de pensum | Nuevo tipo de documento (migración `catalog 0004`), solo quinto bachillerato; consolidado de notas finales por curso y por año, con promedio anual y general (`grading/services/consolidado.py`). |
| 7 | Buzón | `sender_label`: el lado administrativo ve «Usuario familia - <estudiante>»; el portal de familia muestra «Tú», estado del hilo y formulario plegable. |
| 8 | Asistencia móvil | Calendario mensual (lunes a viernes) con resumen y navegación por mes, en vez de lista. |
| 9 | Docente solo lectura | Docente pasa a `ver` en Asistencia (migración `accounts 0003`); `docs/permisos-roles.md` al día. |
| 10 | Reporte de conducta | Nace en borrador; Dirección lo publica (`POST /conduct-reports/{id}/publish/`); la familia solo ve publicados y los ve en tarjetas con PDF. Los existentes quedan publicados. |

## Verificación

- Backend: 529 pruebas pasan, `ruff` limpio.
- Frontend: typecheck, lint y 69 pruebas unitarias.
- Playwright en vivo (base reiniciada): `asistencia`, `horarios`, `comunicacion`, `portal-publico`.
- No se ejecutó el resto de las specs ni se vio el PDF de cierre de pensum con datos reales (solo prueba automática de generación).

## Al desplegar

Las migraciones corren solas (`accounts 0003`, `catalog 0004`, `communication 0003`). La spec `portal-publico` dependía de que fuera lunes; ahora usa la fecha de hoy.
