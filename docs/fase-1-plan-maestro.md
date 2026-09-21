# Fase 1 — Plan maestro

Cierre de la Fase 1 según el plan de fases (sección 18 del prompt maestro). Documentación únicamente, cero código.

## Entregables de esta fase

| Documento | Contenido |
|---|---|
| [`modelo-datos.md`](modelo-datos.md) | Modelo físico de las 26 tablas (25 entidades + `GuardianStudentLink`), con diagrama entidad-relación |
| [`arquitectura.md`](arquitectura.md) | Mapa de módulos del backend y del frontend, contrato de capas, rutas por portal |
| [`api.md`](api.md) | Contrato de la API por app, previo al esquema OpenAPI que se generará desde el código |
| [`permisos-roles.md`](permisos-roles.md) | Matriz de 8 roles contra 15 áreas de permiso, con 3 preguntas pendientes de confirmar |
| [`trazabilidad.md`](trazabilidad.md) | Los 37 RF, más RN y RNF sin RF único, mapeados a módulo, endpoint y prueba prevista |
| [`adr/0001-modelado-talleres-como-seccion.md`](adr/0001-modelado-talleres-como-seccion.md) | Talleres comparten Sección/Inscripción con la jornada matutina |
| [`adr/0002-relacion-encargado-estudiante.md`](adr/0002-relacion-encargado-estudiante.md) | Tabla intermedia `GuardianStudentLink`, parentesco movido al vínculo |
| [`adr/0003-redondeo-nota-final.md`](adr/0003-redondeo-nota-final.md) | Propuesta de redondeo aritmético estándar y RN-04 como regla flexible — **pendiente de confirmar** |
| [`adr/0004-bitacora-de-cambios-formato.md`](adr/0004-bitacora-de-cambios-formato.md) | Bitácora única en `core/`, valores antes/después en JSON |
| [`adr/0005-bibliotecas-pdf-qr-plantillas.md`](adr/0005-bibliotecas-pdf-qr-plantillas.md) | Propuesta de WeasyPrint, qrcode y openpyxl — **pendiente de confirmar antes de instalar** |

## Decisiones ya resueltas con las respuestas de la Fase 0

- Talleres con Sección/Inscripción compartida, sección única cuando el taller tiene un solo grupo.
- Un estudiante puede tener más de un encargado con cuenta propia; el parentesco vive en el vínculo, no en el encargado.
- Los talleres no generan actividades ni calificaciones, solo asistencia.
- Repositorio conectado a `https://github.com/kostritzer24/Ando.git`, rama `main` (push pendiente de que lo ejecutes tú — el clasificador de permisos de la sesión bloqueó el push automático).
- Sin datos históricos que migrar al inicio; se prevé una importación posterior desde Excel (afecta el diseño de `grading`/`attendance` template upload, que ya está pensado para carga masiva).
- Logo institucional recibido y colores de marca extraídos por muestreo de píxeles, para usarlos en la Fase 2:

  | Color | Valor aproximado |
  |---|---|
  | Azul | `#2AA9E0` |
  | Verde | `#68B840` |
  | Amarillo | `#F8C018` |
  | Rojo | `#E83838` |

  Estos son los cuatro colores de las cintas del hexágono y coinciden con el azul del nombre "EL PATOJISMO" y el rojo de "SUEÑOS E IDEAS EN ACCIÓN". La paleta completa (con neutros de texto y fondo, y su verificación de contraste WCAG AA) se arma formalmente en la Fase 2, no en esta.

## Pendiente de confirmación antes de avanzar a la Fase 2

1. **Coordinación:** su nivel de edición exacto en Avisos y Reportes de conducta no está definido en el Capítulo IV (`docs/permisos-roles.md`, sección "Pendientes"). Se implementó con `V` por defecto en todo lo administrativo hasta que se confirme.
2. **Administrador del sistema y datos sensibles:** RNF-04 solo menciona a Dirección; se dejó sin acceso a salud/datos socioeconómicos para el Administrador, salvo que dirección indique lo contrario.
3. **Redondeo de la nota final** (ADR-0003): se propone redondeo aritmético estándar; hay que confirmarlo antes de que se implemente en la Fase 7, porque no es corregible después de publicar boletines sin republicar.
4. **Bibliotecas de PDF, QR y plantillas** (ADR-0005): se proponen WeasyPrint, `qrcode` y `openpyxl`; no se instalan hasta que se confirmen.
5. **Formato del código interno del estudiante** (`internal_code`): no especificado en el Capítulo IV; se decidirá en la Fase 5 junto con el caso de uso de inscripción.

## Punto de control

Con esto se cierra la Fase 1. Antes de iniciar la Fase 2 (dirección visual), se necesita:

- Confirmación o corrección de los 5 puntos pendientes de arriba, o autorización para avanzar con las propuestas tal como están documentadas.
- Autorización explícita para pasar a la Fase 2.
