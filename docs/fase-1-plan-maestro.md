# Fase 1 — Plan maestro

Cierre de la Fase 1 según el plan de fases (sección 18 del prompt maestro). Documentación únicamente, cero código.

## Entregables de esta fase

| Documento | Contenido |
|---|---|
| [`modelo-datos.md`](modelo-datos.md) | Modelo físico de 27 tablas (25 entidades del Capítulo IV + `GuardianStudentLink` + `ConductRuleArticle`/`ConductReportArticle` de ADR-0006), con diagrama entidad-relación |
| [`arquitectura.md`](arquitectura.md) | Mapa de módulos del backend y del frontend, contrato de capas, rutas por portal |
| [`api.md`](api.md) | Contrato de la API por app, previo al esquema OpenAPI que se generará desde el código |
| [`permisos-roles.md`](permisos-roles.md) | Matriz de 8 roles contra 15 áreas de permiso |
| [`trazabilidad.md`](trazabilidad.md) | Los 37 RF, más RN y RNF sin RF único, mapeados a módulo, endpoint y prueba prevista |
| [`adr/0001-modelado-talleres-como-seccion.md`](adr/0001-modelado-talleres-como-seccion.md) | Talleres comparten Sección/Inscripción con la jornada matutina |
| [`adr/0002-relacion-encargado-estudiante.md`](adr/0002-relacion-encargado-estudiante.md) | Tabla intermedia `GuardianStudentLink`, parentesco movido al vínculo |
| [`adr/0003-redondeo-nota-final.md`](adr/0003-redondeo-nota-final.md) | Redondeo aritmético estándar y RN-04 como regla flexible — **aceptado** |
| [`adr/0004-bitacora-de-cambios-formato.md`](adr/0004-bitacora-de-cambios-formato.md) | Bitácora única en `core/`, valores antes/después en JSON |
| [`adr/0005-bibliotecas-pdf-qr-plantillas.md`](adr/0005-bibliotecas-pdf-qr-plantillas.md) | WeasyPrint, `qrcode` y `openpyxl` — **aceptado** |
| [`adr/0006-formato-reporte-conducta.md`](adr/0006-formato-reporte-conducta.md) | `ConductReport` estructurado según `docs/reporte.docx`, nuevo catálogo de artículos del código de convivencia |

## Decisiones resueltas en el cierre de esta fase

- Talleres con Sección/Inscripción compartida, sección única cuando el taller tiene un solo grupo; no generan notas, solo asistencia (ADR-0001).
- Un estudiante puede tener más de un encargado con cuenta propia; el parentesco vive en el vínculo, no en el encargado (ADR-0002).
- **Redondeo de la nota final: confirmado, aritmético estándar** (ADR-0003, aceptado).
- **Administrador del sistema: puede ver (no editar) los datos sensibles de salud y socioeconómicos**, confirmado por dirección — se actualizó `permisos-roles.md` (nota 9) y `api.md`. Toda consulta queda en `core.AccessLog`.
- **Bibliotecas de PDF, QR y plantillas: confirmadas** — WeasyPrint, `qrcode`, `openpyxl` (ADR-0005, aceptado). Se instalan al armar `requirements/base.txt` en la Fase 3.
- **Formato del reporte de conducta:** se recibió `docs/reporte.docx` (formato real "Reporte de incidencia" del centro) y se incorporó al modelo — `ConductReport` ahora tiene columnas estructuradas para tipo de falta, artículos incumplidos, sanción y compromisos, más un catálogo nuevo `ConductRuleArticle` (ADR-0006). Este documento resultó ser el formato del **reporte de conducta (RF-24/RF-35)**, no un reporte institucional genérico de la sección 11.
- Repositorio conectado a `https://github.com/kostritzer24/Ando.git`, rama `main` (push pendiente de que lo ejecutes vos — el clasificador de permisos de la sesión bloquea el push automático).
- Logo institucional recibido; paleta de marca extraída por muestreo de píxeles para la Fase 2:

  | Color | Valor aproximado |
  |---|---|
  | Azul | `#2AA9E0` |
  | Verde | `#68B840` |
  | Amarillo | `#F8C018` |
  | Rojo | `#E83838` |

## Pendiente de confirmación (no bloquea el inicio de la Fase 2)

1. **Coordinación:** su nivel de edición exacto en Avisos y Reportes de conducta sigue sin definirse — no llegó respuesta sobre este punto específico. Se mantiene `V` por defecto en `permisos-roles.md` hasta que se confirme.
2. **Formato del `internal_code` de Estudiante — contradicción numérica sin resolver.** Indicaste el formato `ES01`, `ES02` (dos dígitos), pero dos dígitos solo alcanzan para 99 estudiantes y el centro ya tiene 144 en la jornada matutina más talleres. Se fijó provisionalmente en `modelo-datos.md` como `ES` + 3 dígitos (`ES001`...) para que el modelo no quede roto, pero es una corrección del equipo técnico, no tu confirmación literal — hay que validarla antes de la Fase 5. Si el `01`/`02` significaba otra cosa (por ejemplo, sección o año de ingreso en vez de secuencial), avisame y se ajusta.

## Punto de control

Con esto se cierra la Fase 1. Se avanza a la Fase 2 (dirección visual) con las dos preguntas pendientes de arriba abiertas pero no bloqueantes, tal como se me indicó ("continuamos").
