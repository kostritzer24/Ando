# Fase 0 — Lectura y preguntas

Lectura completa de `docs/PROMPT_MAESTRO.md` (Capítulo IV del anteproyecto). Sin código en esta fase, según la regla de trabajo 1 y el cierre de la Fase 0 en el plan de fases.

---

## 1. Preguntas abiertas

Ordenadas por lo que más bloquea el avance hacia la Fase 1 (modelo de datos y plan maestro).

### Bloquean el modelo de datos (Fase 1)

1. **¿Los talleres de la tarde usan la misma estructura de Sección/Inscripción que la jornada matutina, o es un mecanismo de registro distinto?** Las 25 entidades no incluyen una tabla separada para "participante de taller". Curso tiene un atributo `tipo` que podría distinguir "académico" de "taller", pero Sección se describe con `grado, letra, tipo` — no queda claro si un taller tiene su propia "sección" (p. ej. "Taller de panadería — grupo único") o si el participante se inscribe directo al Curso sin pasar por Sección. Esto determina si Inscripción, Asistencia y Calificación aplican igual a los ~40 participantes de talleres o si necesitan una variante.
2. **¿Un estudiante puede tener más de un Encargado con cuenta propia?** (p. ej. madre y padre, cada uno con su usuario). El modelo lista Encargado con un campo `usuario` (singular) y RF-04 dice "vincular a un encargado con uno o varios estudiantes", pero no dice si la relación Encargado↔Estudiante es muchos-a-muchos en ambos sentidos. Esto define si hace falta una tabla intermedia explícita y si dos cuentas distintas pueden ver al mismo estudiante.
3. **¿Los talleristas califican algo, o el taller es solo asistencia?** RF-16 y RF-21 cubren asistencia de talleres; ningún RF menciona notas de taller. Si un tallerista nunca define Actividades ni Calificaciones, el modelo de Asignación docente / Actividad debería dejarlo fuera desde el diseño, no solo por permisos.

### Bloquean la Fase 2 (dirección visual)

4. **Falta el logo y la paleta de colores institucional de El Patojismo**, requeridos explícitamente por RNF-08 y por la sección 15.1 del documento ("pide al equipo el logo y la paleta institucional... deriva de ahí, no de una paleta genérica"). Sin esto no se puede iniciar la Fase 2 conforme a la instrucción.

### Bloquean cimientos técnicos (Fase 3) pero no el diseño

5. **¿Ya existe un repositorio remoto en GitHub para el proyecto?** Si sí, necesito la URL y si debo usarlo directamente o crear uno nuevo. Si no existe, ¿bajo qué cuenta/organización se crea y quién más necesita acceso (los ingenieros revisores de la facultad)?
6. **¿Existen ya proyectos creados en Render y en Neon**, o se dejan configurados para que el equipo los cree en la Fase 14? Afecta si preparo nombres de variables de entorno genéricos o si integro credenciales reales más adelante.
7. **¿Hay datos históricos** (notas, asistencia, pagos) en las hojas de cálculo y cuadernos actuales que deban migrarse al arrancar en producción, o el sistema inicia en blanco con el ciclo escolar vigente? Si hay migración, es un proceso adicional no descrito en las 14 fases.
8. **Cuenta de administrador inicial:** ¿quién es la persona (encargado del laboratorio) que recibirá el primer usuario de Administrador del sistema, y con qué nombre de usuario se crea en el entorno de producción? En desarrollo se usará un usuario de siembra ficticio de todas formas.

### No bloquean, pero conviene confirmar temprano

9. Confirmo el supuesto de zona horaria `America/Guatemala` e idioma único (español de Guatemala) para toda fecha, hora y mensaje del sistema, salvo objeción.
10. RN-04 dice "cuatro pruebas cortas de 10 puntos" — ¿son siempre exactamente 4 actividades de tipo "prueba corta" por unidad y curso, con los 60 puntos restantes repartidos en cualquier número de actividades adicionales que el docente decida? Asumo que sí; lo marco para confirmar en la Fase 1 al definir el dominio de Actividad.

---

## 2. Supuestos de trabajo mientras no se respondan

Cada uno queda además como `TODO(confirmar)` en el documento de Fase 1 correspondiente.

| # | Supuesto | Se usará hasta que se confirme |
|---|---|---|
| 1 | Talleres comparten el modelo de Sección/Inscripción; una Sección de tipo "taller" tiene un solo grupo por Curso-taller y ciclo. | Diseño del modelo físico en Fase 1 |
| 2 | Un Estudiante puede tener varios Encargados vinculados (relación muchos-a-muchos), cada uno con su propio Usuario. | Diseño de Encargado/Estudiante en Fase 1 |
| 3 | Los talleres no generan Calificación ni Actividad; solo Asistencia. La Asignación docente de un tallerista no habilita el módulo de notas. | Reglas de permisos y dominio en Fase 3/7 |
| 4 | El repositorio se inicializa localmente con `git init` (ya hecho) y se conecta a un remoto de GitHub cuando el equipo confirme cuenta/organización. | Configuración de repositorio |
| 5 | No hay datos históricos que migrar; el sistema arranca con el ciclo escolar vigente y datos de siembra ficticios para demostración. | Alcance de la Fase 14 |
| 6 | Zona horaria `America/Guatemala`, idioma único español de Guatemala en toda la aplicación. | Configuración base en Fase 3 |
| 7 | Exactamente 4 actividades de tipo "prueba corta" (10 puntos cada una) por unidad y curso; el resto de actividades sale a discreción del docente hasta completar 100. | Validación de dominio en Fase 7 |
| 8 | La paleta y tipografías de la Fase 2 se construyen con una paleta institucional provisional inspirada en los colores típicos de instituciones educativas guatemaltecas, y se reemplaza en cuanto llegue el logo real. No se avanza a construir pantallas finales de producción con esta paleta provisional. | Fase 2, hasta recibir el logo |

---

## 3. Estructura de carpetas propuesta para el repositorio

```
el-patojismo-cdo/
├── backend/
│   ├── config/                     # settings por entorno (local, pruebas, producción), urls raíz, wsgi/asgi
│   ├── apps/
│   │   ├── accounts/                # Usuario, Rol, autenticación, permisos por rol
│   │   ├── core/                    # transversal: bitácora, registro de acceso, PDF, QR, plantillas, errores, paginación
│   │   ├── catalog/                 # datos maestros: ciclos, unidades, secciones, cursos, tipos de actividad/justificación/documento, becas
│   │   ├── students/                # Estudiante, Encargado, Inscripción
│   │   ├── scheduling/              # Asignación docente, Bloque de horario, Evento de calendario
│   │   ├── attendance/              # Asistencia, Justificación
│   │   ├── grading/                 # Actividad, Calificación, Modificación de nota, boletines
│   │   ├── payments/                # Pago, Beca, solvencia, constancias
│   │   ├── documents/                # Documento emitido, verificación por QR
│   │   ├── communication/           # Aviso, Reporte de conducta, Mensaje de buzón
│   │   └── reports/                  # las 8 consultas institucionales + métricas del estudio
│   ├── manage.py
│   ├── requirements/
│   │   ├── base.txt
│   │   ├── local.txt
│   │   └── production.txt
│   └── pytest.ini
├── frontend/
│   ├── src/
│   │   ├── app/                     # arranque, router, guards, interceptores de Axios
│   │   ├── pages/
│   │   │   ├── administrativo/
│   │   │   ├── operativo/
│   │   │   └── publico/
│   │   ├── features/                # asistencia, notas, horarios, pagos, documentos, calendario, avisos, buzon, reportes
│   │   │   └── <feature>/
│   │   │       ├── api/
│   │   │       ├── components/
│   │   │       ├── composables/
│   │   │       └── stores/
│   │   ├── shared/                  # componentes de interfaz, utilidades, tipos comunes
│   │   └── design/                  # tokens, estilos base, tipografía
│   ├── public/
│   ├── index.html
│   ├── vite.config.ts
│   └── tsconfig.json
├── docs/
│   ├── PROMPT_MAESTRO.md
│   ├── fase-0-lectura-preguntas.md
│   ├── arquitectura.md
│   ├── modelo-datos.md
│   ├── api.md
│   ├── seguridad.md
│   ├── despliegue.md
│   ├── pruebas.md
│   ├── trazabilidad.md
│   ├── manual-direccion.md
│   ├── manual-docente.md
│   ├── manual-padres.md
│   ├── adr/
│   └── diseno/
├── .github/
│   └── workflows/
│       └── ci.yml
├── .env.example
├── .gitignore
└── README.md
```

Notas sobre la estructura:

- Los nombres de app en `backend/apps/` agrupan varias de las 25 entidades por área funcional, no una app por entidad — así una regla de negocio y sus pruebas quedan juntas con el modelo que la usa, en línea con la arquitectura por capas de la sección 12.1.
- `catalog` concentra los siete datos maestros parametrizables (sección 9) porque comparten el mismo patrón de administración (CRUD con baja lógica) y no lo bastante peso individual para apps separadas.
- `scheduling` agrupa Asignación docente, Bloque de horario y Evento de calendario porque las tres reglas relacionadas (RN-13, RN-17, validación de cruces) dependen unas de otras.
- Cada app de `backend/apps/` sigue el patrón `api/ services/ domain/ selectors/ models.py tests/` de la sección 12.1 desde que se cree en la Fase 3.

---

## 4. Traducción de las 25 entidades

| Entidad (documento) | Modelo Django (app.Modelo) | Nombre visible al usuario (verbose_name) |
|---|---|---|
| Ciclo escolar | `catalog.SchoolCycle` | Ciclo escolar |
| Unidad | `catalog.GradingUnit` | Unidad |
| Sección | `catalog.Section` | Sección |
| Curso | `catalog.Course` | Curso |
| Asignación docente | `scheduling.TeacherAssignment` | Asignación docente |
| Bloque de horario | `scheduling.ScheduleBlock` | Bloque de horario |
| Actividad | `grading.Activity` | Actividad evaluativa |
| Calificación | `grading.Grade` | Calificación |
| Modificación de nota | `grading.GradeChangeRequest` | Modificación de nota |
| Estudiante | `students.Student` | Estudiante |
| Encargado | `students.Guardian` | Encargado |
| Inscripción | `students.Enrollment` | Inscripción |
| Asistencia | `attendance.Attendance` | Asistencia |
| Justificación | `attendance.Justification` | Justificación de falta |
| Pago | `payments.Payment` | Pago |
| Beca | `payments.Scholarship` | Beca |
| Documento emitido | `documents.IssuedDocument` | Documento emitido |
| Evento de calendario | `scheduling.CalendarEvent` | Evento de calendario |
| Aviso | `communication.Announcement` | Aviso |
| Reporte de conducta | `communication.ConductReport` | Reporte de conducta |
| Mensaje de buzón | `communication.Message` | Mensaje de buzón |
| Usuario | `accounts.User` | Usuario |
| Rol | `accounts.Role` | Rol |
| Bitácora de cambios | `core.AuditLog` | Bitácora de cambios |
| Registro de acceso | `core.AccessLog` | Registro de acceso |

---

## 5. Riesgos técnicos y mitigación propuesta

| # | Riesgo | Mitigación propuesta |
|---|---|---|
| 1 | **Filtro de propiedad mal implementado** (RNF-04): cambiar un identificador en la URL expone el expediente de otro menor. Es la falla más grave posible según la sección 14.2. | Centralizar el scoping por objeto en clases de permiso reutilizables en `core/`, aplicado siempre a nivel de queryset y nunca por comparación directa contra un parámetro de URL; una prueba de acceso no autorizado obligatoria por recurso (ya exigida en la sección 16), revisada en cada PR que toque un ViewSet. |
| 2 | **Suspensión por inactividad en el plan gratuito de Render**: el portal público puede mostrar una pantalla en blanco mientras el backend despierta. | Pantalla de carga explícita en el frontend con mensaje ("cargando información, puede tardar unos segundos") y reintento automático con backoff, en vez de una pantalla vacía; documentar la limitación en `docs/despliegue.md` como ya pide la sección 17. |
| 3 | **Condiciones de carrera al guardar notas u horarios** cuando dos personas escriben al mismo tiempo (p. ej. dos docentes cargando plantillas de la misma sección). | Transacciones atómicas en la capa de servicios, restricciones únicas a nivel de base de datos (`unique_together`, `CheckConstraint`) en vez de solo validación en Python. |
| 4 | **Plantillas de calificaciones/asistencia subidas por el usuario** (RF-20, RF-21): riesgo de fórmulas, macros o archivos disfrazados. | Leer solo valores calculados (no fórmulas) con la biblioteca que se decida en ADR, validar tipo real de archivo (no solo la extensión), límite de tamaño, procesamiento en memoria sin persistir el archivo original ni ejecutar su contenido — ya exigido en la sección 14.4. |
| 5 | **Redondeo de la nota final (RN-02) ambiguo**: sin especificar el método de redondeo, la nota mostrada en el boletín puede no coincidir con la de "puntos faltantes para aprobar". | Fijar el criterio de redondeo en un ADR antes de programar `domain/grading`, implementarlo como función pura con pruebas de casos límite (promedios que terminan en .5), y que sea la única función que calcule la nota final en todo el sistema. |
| 6 | **Reglas de tiempo cruzadas para habilitar el boletín** (RN-09 + RN-10: solvencia + plazos de entrega): fácil de desalinear si cada módulo calcula la elegibilidad por su cuenta. | Un único servicio de dominio de "elegibilidad del boletín" en `grading/domain/`, consumido por la API, la generación de PDF y el portal público — nunca duplicado. |
| 7 | **Enlaces de descarga de PDF sin caducidad** podrían filtrar documentos con datos de menores si se comparten. | Enlaces firmados de corta duración detrás de la misma autorización que el recurso, nunca servidos desde una carpeta pública — ya exigido en la sección 14.2. |
| 8 | **Límites del plan gratuito de Neon** (conexiones, cómputo) bajo carga puntual, por ejemplo cuando varias secciones cargan boletines el mismo día. | Pool de conexiones configurado explícitamente, pruebas de carga básicas en la Fase 13, monitorear los límites del plan y documentarlos. |
| 9 | **Crecimiento indefinido de la bitácora y el registro de acceso** (RNF-06, RNF-07) puede degradar el rendimiento de reportes con el tiempo. | Índices sobre `(entidad_afectada, fecha)` y `(usuario, fecha)` desde el diseño inicial; dejar documentada (sin implementar todavía) una estrategia futura de purga o archivado, ya que no está pedida en el alcance actual. |
| 10 | **Ambigüedad talleres vs. jornada matutina en el modelo de datos** (ver pregunta 1 y 3): si se resuelve mal, corregirlo después implica migraciones de datos reales de asistencia. | Resolver esta pregunta explícitamente antes de cerrar el modelo físico en la Fase 1, en vez de asumir en silencio; dejarlo como primer punto del ADR de modelado de Inscripción. |

---

## Cierre de la Fase 0

Con esto se completa el entregable de la Fase 0: preguntas abiertas, supuestos, estructura de carpetas, tabla de entidades y riesgos con mitigación. No se escribió código.

Punto de control: se espera aprobación explícita, o respuesta a las preguntas de la sección 1, antes de iniciar la Fase 1 (modelo físico de datos, diagrama, mapa de módulos, contrato de API, matriz de roles y primeros ADR).
