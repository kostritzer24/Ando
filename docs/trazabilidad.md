# Trazabilidad de requerimientos

Enlaza cada requerimiento funcional con sus historias de usuario o reglas de negocio relacionadas, el módulo del backend que lo implementa, el endpoint del contrato (`docs/api.md`) y la prueba prevista — conforme a la regla de trabajo 11 y a la sección 19 del prompt maestro.

**Convención de nombres de prueba** (se fija aquí para que el código la respete desde la Fase 3 en adelante):

- Pruebas de API por RF: `backend/apps/<app>/tests/test_<rf>_<slug>.py`. Cada una incluye, cuando el recurso es de acceso restringido, un caso adicional de acceso no autorizado (sección 16 del prompt maestro) en el mismo archivo o en `test_<rf>_<slug>_acceso_no_autorizado.py`.
- Pruebas de dominio por RN: `backend/apps/<app>/domain/tests/test_<rn>_<slug>.py`, con el código de la regla en el nombre, como exige la sección 16.
- Pruebas de extremo a punta (Playwright): `frontend/e2e/<flujo>.spec.ts`, para los seis flujos de la sección 16.

Este documento se reconstruye desde el código a medida que avanza cada fase; lo que sigue es la planeación previa a la implementación.

## Portal administrativo

| RF | Requerimiento | HU / RN | Módulo | Endpoint | Prueba prevista |
|---|---|---|---|---|---|
| RF-01 | Crear usuarios y asignar rol | — | `accounts` | `POST/PATCH /users/` | `test_rf01_crear_usuario_asigna_rol.py` |
| RF-02 | Administrar datos maestros | HU-02 | `catalog` | `CRUD /cycles/`, `/cycles/{id}/units/`, `/sections/`, `/courses/`, etc. | `test_rf02_hu02_catalogo_ciclos.py`, `test_rf02_catalogos_simples.py` (6 catálogos parametrizados), `test_rf02_unidad_fechas_calculadas.py` (RN-10), `test_rf02_seccion_maestro_guia.py` (ADR-0001) |
| RF-03 | Inscribir estudiantes | HU-03 | `students` | `POST /students/`, `POST /enrollments/` | `test_rf03_hu03_inscripcion_codigo_unico.py` |
| RF-04 | Vincular encargado con estudiantes | ADR-0002 | `students` | `POST /guardians/{id}/link-student/` | `test_rf04_vincular_encargado_estudiante.py` |
| RF-05 | Asignar docentes, talleristas y maestro guía | HU-05 | `scheduling` | `POST /assignments/` | `test_rf05_hu05_asignacion_docente_curso.py` |
| RF-06 | Armar horarios validando cruces | HU-06, RN-13 | `scheduling` | `POST /schedule-blocks/` | `test_rf06_hu06_rn13_cruce_horario.py` |
| RF-07 | Registrar pagos y calcular solvencia | HU-07, RN-08 | `payments` | `POST /payments/`, `GET /solvency/{id}/` | `test_rf07_hu07_rn08_calculo_solvencia.py` |
| RF-08 | Emitir constancia de solvencia en PDF | — | `payments` | `POST /solvency/{id}/certificate/` | `test_rf08_emision_constancia_solvencia.py` |
| RF-09 | Generar, aprobar y publicar boletines | RN-09, RN-10 | `grading` | `POST /report-cards/generate|approve|publish/` | `test_rf09_rn09_rn10_habilitacion_boletin.py` |
| RF-10 | Autorizar o rechazar modificaciones de nota | RN-05 | `grading` | `POST /grade-change-requests/{id}/approve|reject/` | `test_rf23_rf10_modificacion_notas.py` |
| RF-11 | Emitir constancias y cartas membretadas | HU-08, HU-11 | `documents` | `POST /documents/issue/` | `test_rf11_hu08_hu11_emision_documento.py` |
| RF-12 | Justificaciones de faltas y resolución | RN-12 | `attendance` | `CRUD /justifications/`, `POST .../resolve/` | `test_rf12_rn12_justificacion_falta.py` |
| RF-13 | Publicar avisos en cartelera | HU-36 | `communication` | `POST/GET /announcements/` | `test_rf13_hu36_avisos_vigencia.py` |
| RF-14 | Verificar documento por código QR | HU-14 | `documents` | `GET /verify/{code}/` | `test_rf14_hu14_verificacion_publica_qr.py` |
| RF-15 | Reportes y consultas del centro | sección 11 | `reports` | `GET /reports/*` | `test_rf15_reportes_<nombre>.py` (8 + métricas) |

## Portal operativo

| RF | Requerimiento | HU / RN | Módulo | Endpoint | Prueba prevista |
|---|---|---|---|---|---|
| RF-16 | Asistencia diaria | RN-11 | `attendance` | `POST/GET /attendance/` | `test_rf16_rn11_asistencia_diaria_tardanza.py` |
| RF-17 | Definir actividades evaluativas | RN-01, RN-02, RN-04 (ADR-0003) | `grading` | `POST /activities/` | `test_rf17_rn01_rn02_rn04_definicion_actividades.py` |
| RF-18 | Registrar punteo real y calcular nota de unidad | RN-05 | `grading` | `POST /grades/` | `test_rf18_rn05_punteo_real.py` |
| RF-19 | Generar plantilla de calificaciones | HU-19 | `grading` | `GET /grades/template/{a}/{u}/` | `test_rf19_rf20_rn07_plantilla_notas.py` |
| RF-20 | Cargar plantilla con validación y vista previa | HU-20, RN-07 | `grading` | `POST /grades/template/preview|upload/` | `test_rf19_rf20_rn07_plantilla_notas.py` |
| RF-21 | Plantilla de asistencia de talleres | ADR-0001 | `attendance` | `GET/POST /attendance/template/` | `test_rf21_plantilla_asistencia_talleres.py` |
| RF-22 | Publicar asignaciones en el calendario | RN-17 | `scheduling` | `POST /calendar-events/` | `test_rf22_rn17_edicion_calendario_propio.py` |
| RF-23 | Solicitar corrección de nota | — | `grading` | `POST /grade-change-requests/` | `test_rf23_rf10_modificacion_notas.py` |
| RF-24 | Reportes de conducta por sección | — | `communication` | `POST /conduct-reports/` | `test_rf24_reporte_conducta.py` |
| RF-25 | Leer y responder el buzón | HU-25 | `communication` | `GET /messages/`, `POST .../reply/` | `test_rf25_hu25_buzon_hilo_visibilidad.py` |
| RF-26 | Consultar horario propio del docente | — | `scheduling` | `GET /schedule/mine/` | `test_rf26_horario_propio_docente.py` |

## Portal público

| RF | Requerimiento | HU / RN | Módulo | Endpoint | Prueba prevista |
|---|---|---|---|---|---|
| RF-27 | Ingresar y seleccionar estudiante | HU-27, ADR-0002 | `accounts`, `students` | `POST /auth/login/`, `GET /me/students/` | `test_rf27_hu27_selector_estudiante.py` |
| RF-28 | Calendario semanal como primera pantalla | — | `scheduling` | `GET /calendar/weekly/` | `test_rf28_calendario_semanal_portal.py` |
| RF-29 | Consultar notas por curso y unidad | RN-06 | `grading` | `GET /grades/?enrollment=` | `test_rf29_rn06_consulta_notas_familia.py` |
| RF-30 | Puntos faltantes para aprobar | HU-30 | `grading` | `GET /grades/missing-points/{id}/` | `test_rf30_hu30_puntos_faltantes.py` |
| RF-31 | Asistencia y faltas, incluidos talleres | ADR-0001 | `attendance` | `GET /attendance/?enrollment=` | `test_rf31_consulta_asistencia_familia.py` |
| RF-32 | Horario de clases del estudiante | — | `scheduling` | `GET /calendar/weekly/` | `test_rf32_horario_estudiante.py` |
| RF-33 | Estado de pagos y descarga de constancia | — | `payments` | `GET /solvency/{id}/`, `GET /documents/{id}/download/` | `test_rf33_consulta_solvencia_familia.py` |
| RF-34 | Descargar boletín si está habilitado | RN-09, RN-10 | `grading` | `GET /report-cards/{id}/download/` | `test_rf34_rn09_rn10_descarga_boletin.py` |
| RF-35 | Reportes de conducta del estudiante | — | `communication` | `GET /conduct-reports/?enrollment=` | `test_rf35_consulta_conducta_familia.py` |
| RF-36 | Cartelera de avisos | HU-36 | `communication` | `GET /announcements/` | `test_rf36_consulta_avisos_familia.py` |
| RF-37 | Enviar mensajes al buzón | RF-25 (mismo hilo) | `communication` | `POST /messages/`, `GET /messages/{id}/` | `test_rf37_buzon_familia.py` |

## Reglas de negocio sin RF único (cobertura transversal)

Algunas RN no se agotan en un solo RF y necesitan su propia prueba de dominio, independiente de la prueba de API que las ejercita indirectamente:

| RN | Regla | Módulo de dominio | Prueba prevista |
|---|---|---|---|
| RN-03 | Nota mínima para aprobar: 60 puntos | `grading/domain` | `test_rn02_rn03_scoring.py` |
| RN-13 | Seis períodos de 40 minutos y un receso | `scheduling/domain` | `test_rn13_estructura_jornada.py` |
| RN-14 | Código interno único, cuentas solo por administración | `students/domain`, `accounts/domain` | `test_rn14_generar_codigo_interno.py` |
| RN-15 | Sin firmas ni sellos digitales en documentos | `documents/domain` | `test_rn15_documento_sin_firma_digital.py` |
| RN-16 | Bloqueo temporal por infringir normas del buzón | `communication/domain` | `test_rn16_bloqueo_por_infraccion_buzon.py` |

## Requerimientos no funcionales con prueba dedicada

| RNF | Requerimiento | Cómo se verifica |
|---|---|---|
| RNF-03 | Control de acceso por rol, tres niveles | Suite completa de casos de acceso no autorizado por recurso (uno por endpoint restringido, sección 16) |
| RNF-04 | Aislamiento de datos por familia; datos sensibles solo Dirección | `test_rnf04_aislamiento_datos_familia.py`, `test_rnf04_datos_sensibles_solo_direccion.py` |
| RNF-06 | Bitácora de cambios en notas, pagos y asistencia | `test_rnf06_bitacora_registra_cambio.py` en cada app que la usa |
| RNF-07 | Registro de accesos y documentos emitidos | `test_rnf07_registro_acceso_se_genera.py` |
| RNF-10 | Filtro de palabras inapropiadas en el buzón | `test_rnf10_filtro_palabras_bloqueo_temporal.py` |

## Pendiente al cierre de esta fase

Esta matriz se valida contra el código real al cerrar cada fase (punto de control de la regla de trabajo 2): si una prueba prevista aquí no existe al terminar la fase correspondiente, la fase no se da por cerrada.
