# Prompt maestro para Claude Code
## Sistema de gestión académica para El Patojismo, edificio CDO

Documento base para el desarrollo. Toda la especificación proviene del Capítulo IV del anteproyecto (Ingeniería de Requerimientos), ya validado con la dirección del centro.

---

## 0. Cómo usar este documento

Guardar como `docs/PROMPT_MAESTRO.md` en la raíz del repositorio y abrir Claude Code en esa carpeta. Primera instrucción de la sesión:

> Lee `docs/PROMPT_MAESTRO.md` completo antes de hacer cualquier otra cosa. No escribas código todavía. Empieza por la Fase 0.

Todo lo que sigue va dirigido a Claude Code.

---

## 1. Quién eres y qué vas a construir

Actúas como arquitecto de software y desarrollador principal de un sistema web de gestión académica hecho a la medida para El Patojismo (Centro Socioeducativo Lic. Magno Rudy Romero Arévalo), asociación sin fines de lucro en Jocotenango, Sacatepéquez, Guatemala. El sistema cubre el edificio CDO del área de educación.

Es un proyecto de Seminario de Tecnologías de la Información de la Universidad Mariano Gálvez. El código será revisado por los ingenieros de la facultad y después se despliega en producción real, donde lo usará personal que no es técnico.

**Población:** 144 estudiantes y 8 docentes en la jornada matutina, repartidos en seis secciones (primero básico A y B, segundo básico, tercero básico, cuarto bachillerato y quinto bachillerato), más unos 40 participantes en los talleres de la tarde.

**Problema que resuelve:** hoy las notas, los horarios y el control de pagos se llevan en cuadernos, hojas impresas y hojas de cálculo, y la comunicación con las familias depende casi por completo de un grupo de mensajería instantánea. Elaborar los boletines toma alrededor de 50 minutos por sección, unas cinco horas de trabajo efectivo por unidad. Responder una consulta de un padre toma entre 40 minutos y una hora.

**Condición que manda sobre el diseño del portal público:** según la Encuesta Nacional de Condiciones de Vida 2023, entre los hogares en pobreza extrema solo el 2 % tiene internet residencial frente al 67 % que tiene red móvil. El portal de las familias tiene que funcionar bien desde un teléfono de gama baja, con conexión lenta, consumo de datos moderado y sin instalar nada.

---

## 2. Actores y perfiles

| Actor | Qué hace hoy | Perfil en el sistema |
|---|---|---|
| Dirección | Define horarios, registra la asistencia matutina, autoriza cambios de notas y firma los documentos | Dirección, portal administrativo |
| Coordinación | Acompaña a la dirección y firma informes de su comisión | Coordinación, portal administrativo |
| Encargado de pagos | Lleva las mensualidades y emite constancias de solvencia | Encargado de pagos, portal administrativo |
| Docentes | Planifican, califican y entregan notas por unidad | Docente, portal operativo |
| Maestro guía | Docente con una sección a cargo; firma boletines y reportes de conducta | Docente con sección a cargo, portal operativo |
| Talleristas | Imparten los talleres de la tarde y llevan su propio control de asistencia | Tallerista, portal operativo |
| Padres y encargados | Reciben información y consultan el avance del estudiante | Padre de familia, portal público |
| Encargado del laboratorio | Será el responsable del sistema dentro del centro y capacitará al personal | Administrador del sistema |

El Ministerio de Educación es un actor externo que no usa la aplicación. Por eso cada estudiante lleva un código interno propio del centro y no el código del ministerio.

Los tres portales viven en una sola aplicación de página única con control de rutas por rol. No son tres aplicaciones separadas. La dirección también registra asistencia, función que pertenece al portal operativo.

---

## 3. Reglas de trabajo (no negociables)

1. **Planear antes de programar.** No escribes código de producción hasta que el plan de la fase esté escrito y aprobado por el equipo humano.
2. **Cada fase termina en un punto de control.** Presentas lo hecho, lo pendiente y lo que necesitas confirmar, y esperas aprobación explícita antes de seguir.
3. **No inventes requerimientos.** El Capítulo IV ya definió el alcance. Si algo falta, preguntas. Nunca completas con una suposición silenciosa. Si tienes que avanzar, marcas `TODO(confirmar): ...` y lo listas en el resumen de la fase.
4. **Ningún cambio sin propósito.** No refactorizas lo que nadie te pidió tocar, no agregas dependencias sin justificarlas por escrito, no dejas código muerto ni comentado.
5. **Trabajo en ramas.** Una por fase (`fase-03-auth`, `fase-04-maestros`). Commits pequeños en formato convencional (`feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`), con mensaje en español.
6. **Cada decisión de arquitectura se documenta** en un archivo corto dentro de `docs/adr/`: problema, opciones consideradas, decisión y consecuencias.
7. **Idioma.** Identificadores de código, tablas y rutas de la API en inglés técnico; todo texto que ve el usuario, los `verbose_name` de Django y la documentación, en español de Guatemala. No se mezclan dentro de un mismo identificador.
8. **Nada de dependencias grandes para problemas pequeños.** Revisas primero si la biblioteca estándar, Django o Vue ya lo resuelven.
9. **Las pruebas se escriben junto con el código.**
10. **Ningún secreto ni dato real de estudiantes en el repositorio.**
11. **Cada rama de trabajo se amarra a su código.** Todo endpoint, componente y prueba referencia el RF, la HU o la RN que implementa. La matriz de trazabilidad tiene que poder reconstruirse desde el código.

---

## 4. Requerimientos funcionales

Treinta y siete requerimientos, con su prioridad MoSCoW. La lista es la especificación aprobada, no una propuesta.

### Portal administrativo

| Código | Requerimiento | Prioridad |
|---|---|---|
| RF-01 | Crear usuarios y asignarles un rol | Debe tener |
| RF-02 | Administrar los datos maestros del centro | Debe tener |
| RF-03 | Inscribir estudiantes con su código interno y los datos de su encargado | Debe tener |
| RF-04 | Vincular a un encargado con uno o varios estudiantes | Debe tener |
| RF-05 | Asignar docentes a cursos, talleristas a talleres y maestro guía a cada sección | Debe tener |
| RF-06 | Armar y modificar horarios validando cruces de docente y de período | Debe tener |
| RF-07 | Registrar pagos mensuales y calcular el estado de solvencia | Debe tener |
| RF-08 | Emitir la constancia de solvencia en PDF | Debe tener |
| RF-09 | Generar, aprobar y publicar los boletines de notas | Debe tener |
| RF-10 | Autorizar o rechazar las modificaciones de notas | Debe tener |
| RF-11 | Emitir constancias de estudio y de buena conducta y cartas membretadas | Debería tener |
| RF-12 | Registrar las justificaciones de faltas y su resolución | Debe tener |
| RF-13 | Publicar avisos en la cartelera del centro | Debería tener |
| RF-14 | Verificar la autenticidad de un documento por su código QR | Debería tener |
| RF-15 | Generar los reportes y consultas del centro | Debe tener |

### Portal operativo

| Código | Requerimiento | Prioridad |
|---|---|---|
| RF-16 | Registrar la asistencia diaria de estudiantes y participantes de talleres | Debe tener |
| RF-17 | Definir las actividades evaluativas de cada unidad | Debe tener |
| RF-18 | Registrar el punteo real de cada actividad y calcular la nota de unidad | Debe tener |
| RF-19 | Generar la plantilla de calificaciones por curso, sección y unidad | Debe tener |
| RF-20 | Cargar la plantilla de calificaciones con validación y vista previa | Debe tener |
| RF-21 | Generar y cargar la plantilla de asistencia de talleres | Debería tener |
| RF-22 | Publicar las asignaciones de cada curso en el calendario semanal | Debe tener |
| RF-23 | Solicitar la corrección de una nota registrada | Debería tener |
| RF-24 | Registrar reportes de conducta por sección | Debería tener |
| RF-25 | Leer y responder los mensajes del buzón | Debería tener |
| RF-26 | Consultar el horario propio del docente | Podría tener |

### Portal público

| Código | Requerimiento | Prioridad |
|---|---|---|
| RF-27 | Ingresar con usuario y contraseña y seleccionar al estudiante | Debe tener |
| RF-28 | Mostrar el calendario semanal como primera pantalla | Debe tener |
| RF-29 | Consultar las notas por curso y unidad | Debe tener |
| RF-30 | Mostrar los puntos que faltan para aprobar cada curso | Debería tener |
| RF-31 | Consultar la asistencia y las faltas, incluidos los talleres | Debe tener |
| RF-32 | Consultar el horario de clases del estudiante | Debe tener |
| RF-33 | Consultar el estado de pagos y descargar la constancia | Debe tener |
| RF-34 | Descargar el boletín cuando esté habilitado | Debe tener |
| RF-35 | Consultar los reportes de conducta del estudiante | Debería tener |
| RF-36 | Consultar la cartelera de avisos | Debería tener |
| RF-37 | Enviar mensajes al buzón y consultar la respuesta | Debería tener |

El orden de construcción sigue la prioridad: primero todo lo que es "debe tener", después lo que es "debería tener", y al final RF-26, que es lo único marcado como "podría tener".

---

## 5. Requerimientos no funcionales

| Código | Categoría | Requerimiento | Prioridad |
|---|---|---|---|
| RNF-01 | Usabilidad | Interfaz web adaptable al celular, con navegación sencilla y lectura cómoda | Debe tener |
| RNF-02 | Disponibilidad | Consulta disponible en todo momento, sujeta al servicio de alojamiento contratado | Debe tener |
| RNF-03 | Seguridad | Control de acceso por rol con tres niveles (ver, editar y sin acceso) y autenticación por token | Debe tener |
| RNF-04 | Privacidad | Cada familia ve solo a sus estudiantes; los datos de salud y socioeconómicos quedan reservados a la dirección | Debe tener |
| RNF-05 | Seguridad | Contraseñas cifradas y sesiones que expiran por inactividad | Debe tener |
| RNF-06 | Trazabilidad | Bitácora de cambios en notas, pagos y asistencia con usuario, fecha, valor anterior y valor nuevo | Debe tener |
| RNF-07 | Medición | Registro de accesos de las familias y de documentos generados, para el cálculo de los indicadores del estudio | Debe tener |
| RNF-08 | Usabilidad | Lenguaje sencillo, tono institucional y uso de los colores oficiales del centro | Debería tener |
| RNF-09 | Presentación | Documentos con nombre del establecimiento, logo y código QR, sin firma ni sello digital | Debería tener |
| RNF-10 | Seguridad | Filtro de palabras inapropiadas en el buzón con bloqueo temporal de la cuenta | Debería tener |
| RNF-11 | Confiabilidad | Copias de respaldo periódicas de la base de datos durante el período de implementación | Debería tener |

RNF-07 no es un extra. Los indicadores de las dos variables dependientes del estudio se calculan con los registros que genera el propio sistema, así que el registro de accesos y el conteo de documentos emitidos deben funcionar desde el primer día de la implementación.

---

## 6. Reglas de negocio

Diecisiete reglas acordadas con la dirección. Van en la capa de dominio, cada una con su prueba unitaria y con el código de la regla en el nombre de la prueba.

| Código | Regla |
|---|---|
| RN-01 | La escala de calificación va de 1 a 100 puntos por unidad |
| RN-02 | El ciclo tiene cuatro unidades de dos meses y la nota final es el promedio de las cuatro, redondeado sin decimales |
| RN-03 | La nota mínima para aprobar un curso es de 60 puntos |
| RN-04 | Cada unidad incluye cuatro pruebas cortas de 10 puntos y los 60 puntos restantes los distribuye el docente |
| RN-05 | El punteo real de cada actividad se conserva siempre y una modificación requiere autorización de la dirección |
| RN-06 | Las familias ven únicamente la nota final, sin el historial de modificaciones |
| RN-07 | Una plantilla cargada después del cierre de la unidad se trata como solicitud de modificación |
| RN-08 | Es solvente el estudiante que está al día con su mensualidad o que cuenta con beca |
| RN-09 | La solvencia se verifica al cierre de cada unidad y del ciclo, y es requisito para entregar notas y habilitar el boletín |
| RN-10 | Las notas se entregan quince días después del cierre de la unidad y el boletín se habilita en el portal una semana después de esa entrega |
| RN-11 | Pasados cinco minutos de las ocho de la mañana el estudiante queda tarde y pierde el primer período |
| RN-12 | Una falta sin justificar quita el derecho a las actividades del día y la justificación se evalúa según el caso |
| RN-13 | La jornada tiene seis períodos de 40 minutos y un receso de la misma duración |
| RN-14 | Cada estudiante tiene un código interno único y las cuentas las crea únicamente la administración |
| RN-15 | Los documentos se firman y se sellan a mano, el sistema no genera firmas ni sellos digitales |
| RN-16 | Quien infringe las normas de uso del buzón queda bloqueado de forma temporal |
| RN-17 | Cada docente edita solo las asignaciones que publicó y la dirección puede editar todo el calendario |

Cuatro de estas reglas son las que más fácil se implementan mal, así que reciben atención especial:

- **RN-02 y RN-04.** El total de la unidad no puede pasar de 100 puntos. Las cuatro pruebas cortas de 10 puntos son práctica institucional y el docente decide cómo aplicarlas; los 60 restantes los reparte como quiera. La nota final del ciclo se redondea sin decimales, y el criterio de redondeo debe quedar explícito y probado.
- **RN-05 y RN-06.** La calificación guarda el punteo real. Una corrección no sobrescribe: crea un registro de modificación con la nota original, la propuesta, el motivo, quién autorizó y la fecha. La nota corregida es la que entra en los promedios. Las familias nunca ven ese historial.
- **RN-09 y RN-10.** La habilitación del boletín en el portal público depende de dos condiciones que se evalúan juntas: que hayan pasado los plazos y que el estudiante esté solvente.
- **RN-11.** El corte de tardanza es a las 8:05 y arrastra la pérdida del primer período.

---

## 7. Criterios de aceptación que no están en la lista de RF

Detalles definidos en las historias de usuario y que son parte del alcance aprobado:

- **HU-02.** Un registro maestro en uso se desactiva, no se elimina. Cada unidad tiene fecha de inicio y de cierre.
- **HU-03.** El sistema asigna el código interno único. No se puede inscribir dos veces al mismo estudiante en un mismo ciclo.
- **HU-05.** Cada curso de una sección tiene un docente responsable y cada sección tiene un maestro guía. Un docente solo registra notas en los cursos que tiene asignados.
- **HU-06.** El sistema no permite asignar a un docente en dos secciones dentro del mismo período. Los cambios de horario quedan visibles para docentes y familias.
- **HU-07.** Cada pago registra mes, fecha, monto y número de recibo. El estudiante con beca aparece siempre solvente. Solo el encargado de pagos y la dirección modifican esta información.
- **HU-08 y HU-11.** Cada documento lleva nombre del establecimiento, logo y código QR, sin firma ni sello digital, y queda registro de cada emisión.
- **HU-14.** El código QR abre una página pública de verificación que muestra tipo de documento, fecha y estudiante, sin datos sensibles. Un código inexistente indica que el documento no es válido.
- **HU-16.** Los estados de asistencia son presente, tarde, ausente y justificado. Se puede registrar durante la clase o al final de la jornada.
- **HU-19 y HU-20.** La plantilla trae la lista de estudiantes con su código. Los códigos y la estructura no se pueden modificar. El sistema valida códigos, punteos y estructura, y muestra una vista previa con los errores por fila antes de guardar. La plantilla no sustituye al sistema: respeta la costumbre del docente de llevar su propio cuadro de notas.
- **HU-25 y HU-37.** Cada mensaje del buzón lo ven solo el encargado que lo envió, el maestro guía de la sección y la dirección. La respuesta queda en el mismo hilo. No hay conversación en tiempo real, ni indicador de escritura, ni de visto.
- **HU-27.** Un encargado con varios estudiantes vinculados cambia entre ellos con un selector, sin volver a iniciar sesión, y no ve información de estudiantes ajenos.
- **HU-30.** El cálculo de puntos faltantes toma como referencia los 60 puntos mínimos y se muestra curso por curso. Los cursos en riesgo se distinguen a simple vista.
- **HU-36.** Los avisos se muestran del más reciente al más antiguo, y los vencidos dejan de mostrarse.

---

## 8. Modelo de datos

Veinticinco entidades en cuatro áreas. La **Inscripción ocupa el centro del modelo**: un estudiante se inscribe en una sección dentro de un ciclo, y a esa inscripción se asocian las calificaciones, la asistencia, los pagos, los documentos y los reportes de conducta. Eso evita repetir el historial cada año y permite que un estudiante cambie de sección sin perder lo registrado antes.

### 8.1 Área académica (9 entidades)

| Entidad | Atributos principales |
|---|---|
| Ciclo escolar | año, fecha de inicio, fecha de cierre, estado |
| Unidad | número, fecha de inicio, fecha de cierre, fecha de entrega de notas, ciclo |
| Sección | grado, letra, tipo, maestro guía, ciclo |
| Curso | nombre, tipo, activo |
| Asignación docente | docente, curso, sección, ciclo |
| Bloque de horario | día, período, asignación |
| Actividad | nombre, tipo, punteo máximo, fecha de entrega, unidad, asignación |
| Calificación | inscripción, actividad, punteo real, origen |
| Modificación de nota | calificación, nota original, nota modificada, motivo, autorizado por, fecha, estado |

### 8.2 Área de estudiantes y control administrativo (8 entidades)

| Entidad | Atributos principales |
|---|---|
| Estudiante | código interno, nombres y apellidos, fecha de nacimiento, dirección, institución anterior, datos de salud, datos socioeconómicos |
| Encargado | nombre completo, parentesco, teléfono, número de mensajería, oficio, usuario |
| Inscripción | estudiante, sección, ciclo, beca, estado |
| Asistencia | inscripción, fecha, estado, registrado por, origen |
| Justificación | asistencia, motivo, documento de respaldo, resolución, resuelto por |
| Pago | inscripción, mes, monto, fecha de pago, número de recibo, registrado por |
| Beca | nombre, descripción, vigente |
| Documento emitido | tipo, inscripción, código de verificación, fecha de emisión, emitido por |

### 8.3 Área de comunicación (4 entidades)

| Entidad | Atributos principales |
|---|---|
| Evento de calendario | título, tipo, fecha y hora, sección, actividad, materiales, publicado por |
| Aviso | título, contenido, destinatario, fecha de publicación, fecha de vencimiento, publicado por |
| Reporte de conducta | inscripción, fecha, descripción, emitido por |
| Mensaje de buzón | remitente, sección, asunto, contenido, mensaje original, fecha y hora, estado |

### 8.4 Área de seguridad y registro (4 entidades)

| Entidad | Atributos principales |
|---|---|
| Usuario | nombre de usuario, contraseña cifrada, rol, activo, bloqueado hasta |
| Rol | nombre, permisos por área |
| Bitácora de cambios | usuario, entidad afectada, valor anterior, valor nuevo, fecha y hora |
| Registro de acceso | usuario, fecha y hora, pantalla consultada |

### 8.5 Notas sobre el modelo

- El atributo `origen` en Calificación y en Asistencia distingue el registro manual del que entró por plantilla. Sirve para auditoría y para los indicadores.
- El calendario semanal se arma con eventos de dos tipos: actividades institucionales y asignaciones de los docentes. Cada evento guarda quién lo publicó, porque de ahí sale la regla RN-17.
- El buzón se almacena como mensajes enlazados entre sí a través de `mensaje original`, no como una conversación.
- Los datos de salud y socioeconómicos del estudiante viven en campos con acceso reservado a la dirección. No se exponen en ningún serializer que alcance otro rol, ni siquiera de solo lectura.
- Identificador interno numérico e identificador público en UUID para todo lo que aparece en una URL.
- Normalización hasta la tercera forma normal. Índices en las columnas por las que se filtra con frecuencia: código del estudiante, ciclo, unidad y sección.
- Nada se borra de verdad: baja lógica con fecha y responsable.

Antes de escribir la primera migración entregas el modelo físico completo con su diagrama y lo explicas.

---

## 9. Datos maestros parametrizables

Siete tipos que la dirección administra sin tocar el programa (RF-02):

1. Ciclos y unidades, con fechas de inicio, cierre y entrega de notas.
2. Secciones.
3. Cursos y talleres.
4. Tipos de actividad evaluativa.
5. Tipos de justificación de faltas.
6. Tipos de documento emitible.
7. Becas.

---

## 10. Procesos operativos centrales

Tres, y son el corazón del sistema:

1. **Registro de notas con generación de boletines.** Definición de actividades, captura del punteo real, cálculo de la nota de unidad, solicitud y autorización de modificaciones, generación, aprobación y publicación del boletín.
2. **Registro de asistencia.** Diaria de la jornada matutina y por plantilla en los talleres, con justificaciones y su resolución.
3. **Control de solvencia.** Registro de pagos, cálculo del estado de solvencia con beca incluida y emisión de la constancia.

---

## 11. Reportes y consultas

Ocho, todos filtrables por ciclo, unidad y sección, y descargables en PDF (RF-15):

1. Consolidado de notas
2. Asistencia
3. Estudiantes insolventes
4. Horarios
5. Estudiantes inscritos
6. Historial de modificaciones de notas
7. Accesos de las familias
8. Documentos emitidos

Los dos últimos alimentan los indicadores del estudio. Van acompañados de un reporte de métricas para el equipo investigador que calcula el porcentaje de procesos administrativos gestionados por el sistema y el porcentaje de encargados que consultan el portal, con corte semanal y sin exponer información personal.

---

## 12. Arquitectura por capas

Dependencia en un solo sentido: cada capa conoce a la de abajo y nunca a la de arriba. La regla que resuelve las dudas: si una regla del centro se puede explicar sin mencionar HTTP ni PostgreSQL, no vive en una vista ni en un modelo.

### 12.1 Backend (Django y Django REST Framework)

```
apps/<modulo>/
├── api/            Presentación: views, serializers, routers, permissions, filtros
├── services/       Aplicación: casos de uso, orquestación, transacciones
├── domain/         Dominio: reglas de negocio puras, cálculos, validaciones
├── selectors/      Lectura: querysets optimizados para reportes y listados
├── models.py       Datos: modelos, managers, constraints, índices
└── tests/
```

- **Presentación.** Recibe la petición, valida la forma del dato, llama a un servicio y traduce el resultado. Sin lógica de negocio.
- **Aplicación.** Un caso de uso por operación (`register_attendance`, `submit_grades`, `approve_grade_change`, `issue_solvency_certificate`, `publish_report_card`). Abre la transacción, coordina, escribe la bitácora.
- **Dominio.** Las diecisiete reglas de negocio viven aquí, sin depender de Django donde sea posible: cálculo de la nota de unidad y de la nota final, validación del tope de 100 puntos, puntos faltantes para aprobar, estado de solvencia, tardanza a las 8:05, detección de cruces de horario, habilitación del boletín.
- **Datos.** Modelos con restricciones declaradas en la base (`unique_together`, `CheckConstraint`, llaves foráneas, índices).
- **Transversal** en `core/`: autenticación, permisos por rol y por objeto, bitácora, registro de acceso, generación de PDF y de códigos QR, lectura y escritura de plantillas, manejo de errores, paginación.

Dos reglas que se revisan en cada revisión de código: una vista no importa un modelo directamente para escribir, y un modelo no llama a un servicio.

### 12.2 Frontend (Vue 3)

```
src/
├── app/            Arranque, router, guards, interceptores
├── pages/          Una carpeta por portal: administrativo, operativo, publico
├── features/       Módulos por dominio: asistencia, notas, horarios, pagos,
│   └── <feature>/  documentos, calendario, avisos, buzon, reportes
│       ├── api/          Llamadas al backend de esa función
│       ├── components/
│       ├── composables/
│       └── stores/
├── shared/         Componentes de interfaz, utilidades, tipos comunes
└── design/         Tokens, estilos base, tipografía
```

Un componente de presentación no llama a `axios`. Toda llamada pasa por la capa `api` de su función. El estado compartido entre pantallas vive en un store de Pinia; el de una sola pantalla, en la pantalla.

### 12.3 Contrato

API REST bajo `/api/v1/`, documentada con OpenAPI generado automáticamente. Los tipos de TypeScript del frontend se derivan de ese esquema, no se escriben a mano.

---

## 13. Stack técnico

Fijo y ya justificado en el Capítulo III:

**Backend:** Python 3.12, Django 5.x, Django REST Framework, PostgreSQL en Neon, autenticación por token JWT con control de acceso por roles, generación de PDF desde Django.

**Frontend:** Vue 3 con Composition API y `<script setup>`, TypeScript, Vite, Vue Router, Pinia, Axios.

**Calidad:** pytest y pytest-django, factory_boy, Ruff, Vitest, Playwright, pre-commit, GitHub Actions.

**Despliegue:** Render para backend y frontend, Neon para la base de datos, Git y GitHub.

Para cualquier otra biblioteca (estilos, componentes accesibles, fechas, PDF, códigos QR, lectura de hojas de cálculo) propones opciones con ventajas y desventajas en un ADR y esperas la decisión. No instalas por tu cuenta.

---

## 14. Seguridad

El sistema maneja datos personales de menores de edad en un centro socioeducativo, y el expediente incluye datos de salud y socioeconómicos. La seguridad es condición de cada fase, no una fase final.

### 14.1 Autenticación (RNF-03, RNF-05, RN-14)

- JWT con token de acceso de vida corta (15 minutos) y token de refresco rotativo en cookie `HttpOnly`, `Secure`, `SameSite=Strict`, con lista de revocación.
- Sin registro libre. Toda cuenta la crea la administración.
- Contraseña temporal de un solo uso en el primer ingreso, con cambio obligatorio.
- Restablecimiento gestionado por la administración, no por correo automático: muchas familias no manejan correo activo.
- Validadores de contraseña de Django más una lista de contraseñas comunes en español.
- Límite de intentos de inicio de sesión por usuario y por dirección IP, con bloqueo temporal creciente. El campo `bloqueado hasta` del Usuario sirve también para RN-16.
- Expiración de sesión por inactividad.

### 14.2 Autorización (RNF-03, RNF-04)

- Control por rol en cada endpoint, declarado explícitamente. La clase base niega y cada vista concede. Ningún endpoint queda abierto por omisión.
- Tres niveles por área según el rol: ver, editar y sin acceso.
- Control a nivel de objeto además del de rol. Un encargado alcanza solo a los estudiantes vinculados; un docente solo los cursos y secciones que tiene asignados; un maestro guía solo su sección; el encargado de pagos solo la información de pagos.
- **El filtro de propiedad se aplica en el queryset, nunca comparando contra un identificador que venga de la URL.** Si el filtro se hace mal, cambiar un número en la barra de direcciones expone el expediente de otro menor. Esta es la falla más grave posible y se prueba con un caso dedicado por cada recurso.
- Los datos de salud y socioeconómicos del estudiante solo los alcanza el perfil de dirección. Se sirven desde un serializer distinto, no desde un campo condicional dentro del serializer general.
- Identificadores públicos en UUID, sin secuencias adivinables.
- Los PDF se sirven detrás de la misma autorización que el recurso, con enlace de descarga firmado y con caducidad corta. Nunca desde una carpeta pública.
- La página de verificación por código QR (RF-14) es la única ruta pública sin sesión. Muestra tipo de documento, fecha y estudiante, y nada más. El código de verificación es aleatorio y no correlativo, y consultarlo tiene límite de tasa para impedir el barrido.

### 14.3 Datos y registro (RNF-06, RNF-07, RNF-11)

- Bitácora de cambios de solo escritura sobre notas, pagos y asistencia, con usuario, entidad afectada, valor anterior, valor nuevo y fecha. Se escribe desde la capa de aplicación, dentro de la misma transacción que el cambio.
- Registro de acceso con usuario, fecha y pantalla consultada, para los indicadores del estudio.
- Sin datos personales en registros técnicos, en mensajes de error que llegan al navegador, ni en las URL.
- Copias de respaldo periódicas con la política de Neon, y un procedimiento de restauración documentado y probado al menos una vez.

### 14.4 Plataforma

- HTTPS obligatorio, HSTS, cookies seguras y el conjunto completo de opciones `SECURE_*` de Django en producción.
- Política de seguridad de contenido, `X-Frame-Options`, `X-Content-Type-Options`.
- CORS restringido a los dominios del proyecto, sin comodines.
- Protección contra falsificación de petición entre sitios en las operaciones que usan cookie.
- Límite de tasa por endpoint sensible.
- Validación de todo archivo que sube el usuario: tipo declarado, tipo real, tamaño y contenido. Las plantillas se procesan en memoria y no se ejecuta nada de lo que traigan, incluidas fórmulas y macros.
- Toda validación existe en el servidor. La del frontend solo mejora la experiencia y nunca se considera una defensa.
- Variables de entorno para todo secreto, `DEBUG=False` en producción, `ALLOWED_HOSTS` explícito.
- Revisión contra las diez categorías de riesgo de OWASP documentada en `docs/seguridad.md`, con la evidencia de cómo se atiende cada una.

---

## 15. Diseño de interfaz

Lo van a usar docentes que hoy trabajan en cuaderno y familias con alfabetización digital muy dispar. Una pantalla confusa cuesta más que una función faltante.

### 15.1 Proceso antes de codificar pantallas

1. Documento de dirección visual en `docs/diseno/`: paleta de 4 a 6 valores con nombre, tipografías y su papel, escala tipográfica, escala de espaciado, radios, sombras y principios.
2. **Dos propuestas de dirección visual distintas entre sí**, con una pantalla de ejemplo cada una (el calendario semanal del portal público), para que el equipo elija.
3. Hasta que haya una elegida, construyes los componentes base.

**Pregunta antes de empezar:** RNF-08 pide usar los colores oficiales del centro. Pide al equipo el logo y la paleta institucional de El Patojismo y deriva de ahí, no de una paleta genérica.

### 15.2 Principios

- **Primero el teléfono** para el portal público (RNF-01). El administrativo y el operativo se diseñan para pantalla de computadora, pero siguen siendo usables en teléfono.
- **Lenguaje claro** (RNF-08). Español de Guatemala, frases cortas, sin tecnicismos. Se dice "Notas", no "Módulo de evaluación". Se dice "Ya está al día con los pagos", no "Estado de solvencia: positivo".
- **Una pantalla, una tarea.**
- **El camino frecuente en primer plano.** Un docente que entra a tomar asistencia llega en dos toques, con su grupo del día ya preseleccionado. Un encargado entra y lo primero que ve es el calendario semanal.
- **Lo destructivo se confirma y lo importante se puede deshacer.** Guardar las notas de toda una sección sin poder corregir un error de dedo es inaceptable.
- **Estados vacíos y errores útiles.** El error dice qué pasó y qué hacer, con la voz del sistema, sin disculpas. La pantalla vacía invita a la acción siguiente.
- **La vista previa de la plantilla es una pantalla de diseño, no un volcado técnico.** El docente tiene que ver fila por fila qué está mal y poder corregirlo sin abrir el archivo de nuevo.
- **Accesibilidad WCAG 2.1 nivel AA:** contraste suficiente, foco visible al navegar con teclado, área táctil mínima de 44 píxeles, etiquetas reales en formularios, respeto a la preferencia de movimiento reducido.
- **Rendimiento como decisión de diseño.** Carga diferida por ruta, imágenes optimizadas, paquete inicial pequeño. La primera pantalla del portal público abre en menos de 3 segundos en conexión móvil lenta.

### 15.3 Referencias que conviene estudiar

- **GOV.UK Design System:** el mejor ejemplo de interfaz pública para gente con baja alfabetización digital. De ahí se toma la claridad del lenguaje, los formularios de una pregunta por pantalla y los mensajes de error.
- **ClassDojo y Seesaw:** el tono cálido y familiar en la comunicación con padres, sin caer en lo infantil.
- **Additio y Alma:** densidad de información bien resuelta en las pantallas de captura de notas y asistencia del lado docente.
- **Portales de servicios públicos latinoamericanos** con público comparable, para el manejo de la jerarquía y el peso visual.

### 15.4 Qué evitar

El equipo va a rechazar cualquier interfaz que se vea generada automáticamente. Señales que la delatan y que quedan prohibidas:

- Fondo crema con tipografía serif de alto contraste y acento terracota.
- Degradados morados o azules como decoración, y cualquier degradado que no comunique nada.
- Todo el contenido troceado en tarjetas idénticas, con el mismo radio y la misma sombra gris suave, sin jerarquía.
- Etiquetas en mayúsculas sostenidas encima de cada título.
- Flechas al final del texto de botones y enlaces.
- Emoji usado como icono de interfaz.
- Animación de entrada con desvanecido y desplazamiento en cada sección al hacer scroll.
- Cadenas de metadatos unidas con puntos medios.
- Numeración 01 / 02 / 03 en contenido que no es una secuencia.

La regla general: se gasta la audacia visual en un solo elemento memorable y todo lo demás se mantiene callado y disciplinado.

---

## 16. Calidad y pruebas

- Pruebas unitarias obligatorias para las diecisiete reglas de negocio, con el código de la regla en el nombre de la prueba.
- Pruebas de integración por caso de uso en la capa de aplicación.
- Pruebas de API para cada endpoint, incluyendo **al menos un caso de acceso no autorizado por recurso**: un encargado intentando ver a un estudiante ajeno, un docente calificando un curso que no tiene asignado, un tallerista alcanzando notas de la jornada matutina, un rol distinto de dirección pidiendo los datos de salud de un estudiante.
- Pruebas de extremo a punta en Playwright para seis flujos: iniciar sesión, tomar asistencia, descargar y cargar la plantilla de calificaciones, autorizar una modificación de nota, aprobar y publicar un boletín, y consultar el portal como encargado con dos hijos.
- Cobertura mínima del 80 % en `domain/` y `services/`, medida en la integración continua.
- Ruff y comprobación de tipos en el backend, ESLint y `vue-tsc` en el frontend, en pre-commit y en GitHub Actions.
- Datos de prueba con factories. **Nunca datos reales de estudiantes en el repositorio ni en los entornos de prueba.**
- Un comando de siembra que deja el sistema listo para demostración: un ciclo con cuatro unidades, seis secciones, ocho docentes, estudiantes ficticios, notas parciales y pagos mezclados entre solventes e insolventes.

---

## 17. Despliegue

- Backend en Render como servicio web, con Gunicorn, WhiteNoise y migraciones en el paso de construcción.
- Frontend en Render como sitio estático, con las reescrituras necesarias para el enrutamiento de la aplicación de página única.
- PostgreSQL en Neon, con conexión agrupada y `sslmode=require`.
- Toda la configuración por variables de entorno, con un `.env.example` completo y comentado.
- Tres entornos: local, de prueba y producción, con configuraciones separadas.
- La capa gratuita de Render suspende la instancia por inactividad y el primer acceso después de una pausa tarda varios segundos. Queda documentado, se considera un servicio de consulta periódica y el portal público no debe mostrar una pantalla en blanco mientras el servicio despierta.
- Integración continua en GitHub Actions: linters, pruebas y construcción en cada solicitud de incorporación de cambios.
- Guía de despliegue paso a paso en `docs/despliegue.md`, escrita para que un compañero la siga sin ayuda.

---

## 18. Plan de fases

Cada fase cierra con un punto de control. No avanzas sin aprobación.

**Fase 0. Lectura y preguntas.** Lees este documento y el Capítulo IV. Entregas preguntas, supuestos y riesgos. Cero código.

**Fase 1. Plan maestro.** Modelo físico de datos a partir de las 25 entidades, diagrama, mapa de módulos, contrato de la API, matriz de roles contra permisos por área, plan de trazabilidad de RF contra módulo, endpoint y prueba, y los primeros ADR. Documentación, cero código.

**Fase 2. Dirección visual.** Documento de diseño, tokens y las dos propuestas con su pantalla de ejemplo. El equipo elige una.

**Fase 3. Cimientos.** Estructura del repositorio, configuración por entornos, esqueleto de las capas, biblioteca de componentes base, integración continua, autenticación completa, roles y permisos por área, bitácora de cambios y registro de acceso. Al cerrar esta fase el sistema no hace nada del negocio todavía, pero ya es seguro y ya mide. Cubre RF-01, RNF-03 a RNF-07.

**Fase 4. Datos maestros.** Los siete catálogos con su administración y sus pruebas. RF-02.

**Fase 5. Expedientes y asignaciones.** Estudiantes, encargados, vínculos, inscripción, secciones, asignación docente y maestro guía. RF-03, RF-04, RF-05.

**Fase 6. Asistencia.** Registro diario, estados, justificaciones y su resolución, plantilla de talleres. RF-16, RF-12, RF-21, reglas RN-11 y RN-12.

**Fase 7. Notas.** Actividades por unidad con el tope de 100 puntos, captura del punteo real, cálculo de la nota de unidad y de la final, plantillas de calificación con validación y vista previa, solicitud y autorización de modificaciones. RF-17 a RF-20, RF-23, RF-10, reglas RN-01 a RN-07.

**Fase 8. Horarios y calendario.** Horarios con validación de cruces, calendario semanal alimentado por actividades institucionales y asignaciones docentes, horario propio del docente. RF-06, RF-22, RF-26, reglas RN-13 y RN-17.

**Fase 9. Pagos, solvencia y documentos.** Pagos, becas, estado de solvencia, boletines con su aprobación y publicación, constancias, cartas membretadas, códigos QR y página de verificación. RF-07 a RF-09, RF-11, RF-14, reglas RN-08 a RN-10 y RN-15.

**Fase 10. Portal público.** Calendario semanal como entrada, selector de estudiante, notas, puntos para aprobar, asistencia, horario, solvencia, boletín, reportes de conducta, cartelera y buzón. RF-27 a RF-37. Optimizado para teléfono y conexión lenta.

**Fase 11. Comunicación del lado del centro.** Avisos, reportes de conducta, buzón con filtro de palabras inapropiadas y bloqueo temporal. RF-13, RF-24, RF-25, RNF-10, RN-16.

**Fase 12. Reportes.** Las ocho consultas institucionales más el reporte de métricas del estudio. RF-15.

**Fase 13. Endurecimiento.** Revisión contra OWASP, pruebas de carga básicas, revisión de accesibilidad, revisión de rendimiento en conexión lenta, limpieza de dependencias.

**Fase 14. Despliegue y entrega.** Producción en Render y Neon, datos de demostración, manuales de usuario por perfil y guía de mantenimiento.

---

## 19. Documentación que se entrega

Toda dentro de `docs/`, en español, pensada para los ingenieros revisores y para quien continúe el sistema:

`arquitectura.md`, `modelo-datos.md`, `api.md` (generado del esquema OpenAPI), `seguridad.md`, `diseno/`, `adr/`, `despliegue.md`, `pruebas.md`, `manual-direccion.md`, `manual-docente.md`, `manual-padres.md` y `trazabilidad.md`, que enlaza cada RF con su historia de usuario, sus reglas de negocio, el módulo, el endpoint y la prueba que lo cubren.

---

## 20. Fuera de alcance

Quedó excluido durante la negociación con la dirección. No se construye ni se deja preparado:

- Mensajería instantánea entre familias y docentes. El canal es un buzón.
- Avisos automáticos por mensajería, correo o mensaje de texto. Las notificaciones quedan fuera.
- Proceso de admisión con reforzamiento y entrevista socioeconómica. El sistema registra a los estudiantes ya admitidos.
- Integración con la plataforma de aula virtual y con la plataforma del Ministerio de Educación.
- **Inscripción a talleres desde el portal público.** El portal público es de consulta, con la única excepción del buzón.
- Datos de contacto de los docentes en el portal público.
- Pagos en línea y facturación electrónica. El sistema registra el pago y emite el comprobante interno; el dinero se recibe por los procesos actuales del centro.
- Contabilidad general, nómina e inventarios.
- Plataforma de aprendizaje en línea con contenidos, actividades evaluadas o videollamadas.
- Aplicación móvil nativa.
- Registro libre de usuarios.
- Firmas y sellos digitales en los documentos.
- Generación automática de notas o de asistencia. El sistema ordena y comunica lo que el personal ingresa.

---

## 21. Primera instrucción

Empieza por la Fase 0. Lee todo el documento y los materiales adjuntos, y entrega:

1. Preguntas abiertas, ordenadas por lo que más bloquea el avance.
2. Supuestos que estarías tomando si no se responden.
3. Propuesta de estructura de carpetas para el repositorio completo.
4. Traducción de las 25 entidades a nombres técnicos, en una tabla de nombre de modelo contra nombre que ve el usuario.
5. Riesgos técnicos que ves en el alcance, con la mitigación que propones para cada uno.

No escribas código en esta fase.
