# Plan de pruebas manuales

Fuente de verdad de lo que "debe pasar": `docs/PROMPT_MAESTRO.md` (RF, RN, RNF, HU) y `docs/permisos-roles.md` (matriz rol × área). Si algo se siente mal pero **no está documentado**, igual repórtalo como `ux` o `falta-funcionalidad` y dilo en "Referencia": el corrector decidirá con el dueño del proyecto, no inventará requisitos.

## Reparto

| Set | Persona | Módulos | Portales |
|---|---|---|---|
| **A** | | Acceso y sesión, matriz de permisos, usuarios, bitácora, catálogos/ciclos/secciones, reportes institucionales, verificación QR | Todos (transversal) |
| **B** | | Estudiantes, encargados, asignaciones, horarios, calendario, asistencia, justificaciones, plantilla de talleres | Administrativo + Operativo |
| **C** | | Notas (unidad, captura, plantilla, modificaciones) y boletines | Operativo + Administrativo |
| **D** | | Pagos, solvencia, documentos, avisos, reportes de conducta, buzón, portal de familia completo | Administrativo + Operativo + Portal |

## Severidad

| Nivel | Cuándo |
|---|---|
| **Crítica** | Fuga de datos (una familia ve a otra, rol ve lo que no debe), pérdida/corrupción de datos, un proceso central (notas, asistencia, solvencia/boletín) no se puede completar, error 500 |
| **Alta** | Una función "debe tener" no funciona o da resultado incorrecto; bloqueo a un rol; regla RN mal aplicada |
| **Media** | Funciona pero con fallo evidente (validación faltante, mensaje engañoso, estado que no se refresca) |
| **Baja** | Cosmético, texto, alineación, detalle menor |
| **Mejora** | No es error: sugerencia o funcionalidad que se esperaba y no está |

## Hallazgos ya conocidos (no se reportan de nuevo; sí se re-prueban tras el arreglo)

| ID | Qué | Notas / hipótesis |
|---|---|---|
| **K-1** | La sesión no persiste: al cerrar la pestaña/navegador hay que volver a iniciar sesión | Diseño actual: el token de acceso (15 min) vive solo en memoria y se reconstruye con una cookie HttpOnly de refresco (7 días, `SameSite=Strict`, `max_age` fijo). Hipótesis: la cookie no se está guardando o no se envía (host `localhost` vs `127.0.0.1`/IP, `Secure`, `path`, rotación/blacklist del refresh, proxy). **Set A debe diagnosticar con la pestaña Application → Cookies y Network → `/auth/refresh`**. Ojo: el e2e `sesion-persistente` solo prueba recargar, no cerrar y reabrir. |
| **K-2** | Dirección no encuentra dónde editar/gestionar el boletín de notas | Hoy hay `/administrativo/boletines` (generar/aprobar/publicar) y `/administrativo/notas/modificaciones` (aprobar correcciones). Por RN-05 Dirección no sobrescribe notas directo (solo autoriza modificaciones). Falta confirmar si debería haber una vista de notas por sección/curso para Dirección y/o editar. **Set C debe describir qué espera ver un director y qué ve hoy.** |
| **K-3** | RF-30 (puntos que faltan para aprobar) | Documentado como pendiente: sin backend. Solo confirmar que no hay pantalla rota. |

---

## Checklist transversal (TRV) — cada tester lo aplica a **todas sus pantallas**

| ID | Verificar |
|---|---|
| TRV-01 | **Móvil 375 px** (DevTools): sin scroll horizontal de la página, botones tocables, tablas legibles o con scroll propio, menú usable (RNF-01) |
| TRV-02 | **Estados**: cargando (hay indicador), vacío (mensaje útil, no tabla en blanco), error de red (apaga el backend a media pantalla: mensaje claro, no pantalla en blanco) |
| TRV-03 | **Formularios**: campos obligatorios, mensajes de error junto al campo y en español sencillo, no se pierden los datos escritos tras un error, no se envía vacío |
| TRV-04 | **Doble clic / doble envío** en "Guardar/Registrar/Emitir": no duplica registros |
| TRV-05 | **Actualización**: tras crear/editar/borrar, la lista refleja el cambio sin recargar; tras recargar sigue igual |
| TRV-06 | **Navegación**: botón Atrás/Adelante del navegador, recargar (F5) en cada pantalla, enlace directo a la URL interna |
| TRV-07 | **Textos**: español, tono institucional, sin mensajes técnicos/en inglés/`undefined`/`null`/UUIDs visibles, tildes y ñ bien (RNF-08) |
| TRV-08 | **Fechas y números**: formato consistente (dd/mm/aaaa), zona horaria de Guatemala (UTC−6) — probar cerca de medianoche si aplica, moneda con Q y 2 decimales |
| TRV-09 | **Consola del navegador**: sin errores rojos ni warnings de Vue al usar la pantalla |
| TRV-10 | **Red**: en la pestaña Network, ningún 500; los 403/404 deben corresponder a algo que debía negarse |
| TRV-11 | **Teclado/accesibilidad básica**: Tab recorre en orden lógico, foco visible, Enter envía, contraste legible, imágenes con alt |
| TRV-12 | **PDF** (si la pantalla genera uno): abre, no sale cortado, logo + nombre del centro + QR, **sin firma digital** (dos líneas en blanco para firma/sello, RN-15), datos correctos |
| TRV-13 | **Colores/identidad** del centro y consistencia visual entre pantallas (RNF-08) |

---

## SET A — Acceso, seguridad y administración

### Acceso y sesión (RF-27, RNF-03, RNF-05, RN-14)

| ID | Caso | Esperado |
|---|---|---|
| ACC-01 | Iniciar sesión con cada uno de los 8 usuarios | Cada rol cae en su portal (Dirección/Coord/Pagos/Admin → administrativo; Docente/Guía/Tallerista → operativo; Familia → portal) |
| ACC-02 | Contraseña incorrecta; usuario inexistente; campos vacíos | Mensaje claro y **igual** para usuario inexistente y contraseña mala (no revela cuál); no se queda cargando |
| ACC-03 | 11 intentos fallidos en un minuto | Mensaje "Demasiados intentos seguidos"; luego se recupera (RNF-05) |
| ACC-04 | **(K-1)** Iniciar sesión → **cerrar la pestaña** → abrir `localhost:5173` | Debería seguir con sesión. Documentar con evidencia: ¿existe la cookie `refresh_token` en Application → Cookies? ¿con qué `Expires`, `Secure`, `SameSite`, `Path`? ¿qué responde `/auth/refresh`? |
| ACC-05 | Igual pero **cerrar el navegador completo** y reabrir | Ídem |
| ACC-06 | Recargar (F5) en cada portal; entrar por enlace directo a una pantalla interna | Sesión se reconstruye sin ir a `/ingresar` |
| ACC-07 | Dejar la sesión abierta >15 min (o pedir al corrector acortar el token) y seguir usando | El refresco silencioso funciona; no expulsa a media acción ni pierde lo escrito en un formulario |
| ACC-08 | Cerrar sesión; luego botón Atrás | No se ve contenido protegido; manda a `/ingresar` |
| ACC-09 | Cerrar sesión en una pestaña con otra abierta | La otra no debería seguir operando indefinidamente (al menos al siguiente request pide login) |
| ACC-10 | Entrar vía `127.0.0.1:5173` en vez de `localhost:5173` | Documentar si la sesión falla (cookie SameSite/host) |
| ACC-11 | Cambio de contraseña (`/cambiar-contrasena` y en "Cuenta"): reglas de longitud/complejidad, contraseñas que no coinciden, contraseña actual errónea, reutilizar la misma | Mensajes claros; tras cambiar, se puede entrar con la nueva y no con la vieja |
| ACC-12 | Con sesión de un rol, abrir `/ingresar` | Redirige al portal del rol, no muestra login |
| ACC-13 | Rutas inexistentes (`/loquesea`, `/administrativo/zzz`) | Página 404 amable, no pantalla en blanco |

### Matriz de permisos (RNF-03, RNF-04)

| ID | Caso | Esperado |
|---|---|---|
| PER-01 | Para **cada rol**, listar el menú visible y compararlo contra `docs/permisos-roles.md` | Solo aparecen áreas con `ver`/`editar`; nada de más, nada de menos |
| PER-02 | Para cada rol, **escribir a mano** la URL de pantallas de otros portales y de áreas sin acceso (p. ej. `familia.demo` → `/administrativo/usuarios`; `docente.demo` → `/administrativo/pagos`; `pagos.demo` → `/administrativo/notas/modificaciones`) | Redirige/niega con mensaje; nunca renderiza datos |
| PER-03 | Rol con `ver` pero no `editar` (Coordinación en casi todo; Admin en pagos/notas): revisar que **no aparezcan botones de crear/editar/borrar/emitir/aprobar** | Solo lectura real |
| PER-04 | A nivel API: con DevTools copiar un request válido de un rol y reenviarlo con el token de otro rol / sin token (o con `curl`) | 401/403; nunca datos |
| PER-05 | Alcance por objeto: `docente.demo` pidiendo por API una sección/curso que no le asignaron (cambiar el `publicId` de la URL) | 403/404, nunca datos |
| PER-06 | Datos sensibles (salud, socioeconómicos): ver con Dirección (E), Admin (solo ver), resto (sin acceso) | Según matriz; Admin no puede editar |
| PER-07 | Un usuario **desactivado** estando con sesión abierta | Pierde acceso en el siguiente request o al refrescar |

### Usuarios (RF-01, RN-14)

| ID | Caso | Esperado |
|---|---|---|
| USR-01 | Crear usuario por cada rol | Se crea, muestra contraseña temporal una vez, obliga a cambiarla en el primer ingreso |
| USR-02 | Usuario duplicado, correo mal formado, campos vacíos, nombres con tildes/ñ | Validaciones claras |
| USR-03 | Editar nombre/rol; cambiar rol y verificar que el menú del usuario cambia al re-entrar | Correcto |
| USR-04 | Desactivar y reactivar (nunca borrar) | Desactivado no puede entrar; sus datos históricos permanecen |
| USR-05 | Restablecer contraseña | Funciona; contraseña temporal; se registra |
| USR-06 | Quién puede acceder a Usuarios | Solo Dirección y Admin (PER-01) |
| USR-07 | Que alguien pueda quitarse a sí mismo el rol/desactivarse | No debería poder dejar el sistema sin administrador |

### Bitácora y registro de acceso (RNF-06, RNF-07)

| ID | Caso | Esperado |
|---|---|---|
| BIT-01 | Hacer cambios en notas, pagos y asistencia (con otros sets o tú mismo) y revisar Bitácora | Quién, cuándo, valor anterior, valor nuevo |
| BIT-02 | Login de familia y consulta de pantallas | Queda registro de acceso |
| BIT-03 | Emitir un documento | Queda registro de emisión |
| BIT-04 | Filtros, paginación, orden de la bitácora; rendimiento con muchos registros | Usable; Dirección y Admin la ven, nadie más |

### Catálogos, ciclos y secciones (RF-02, HU-02)

| ID | Caso | Esperado |
|---|---|---|
| CAT-01 | Recorrer los 8 catálogos (cursos, tipos de actividad, tipos de justificación, tipos de documento, becas, artículos de convivencia, ciclos, secciones): crear/editar | Funcionan; Coordinación solo ve |
| CAT-02 | Desactivar un registro **en uso** y uno sin uso | Se desactiva (no se elimina); sigue apareciendo en históricos, no en selectores nuevos |
| CAT-03 | Duplicados (mismo nombre), vacíos, textos larguísimos, caracteres especiales | Validación clara, sin 500 |
| CAT-04 | Ciclo: 4 unidades con fecha de inicio y cierre; fechas invertidas, traslapadas, fuera del ciclo | Validación (RN-02, HU-02) |
| CAT-05 | Secciones: crear con maestro guía, tipo académica/taller | Correcto; filtros en otras pantallas la reflejan |
| CAT-06 | Los selectores de otras pantallas (asignaciones, notas) se actualizan al crear un catálogo nuevo | Sin recargar o tras recargar |

### Reportes institucionales y métricas (RF-15)

| ID | Caso | Esperado |
|---|---|---|
| REP-01 | Los 8 reportes: consolidado de notas, asistencia, insolventes (está en Pagos, no aquí), horarios, inscritos, historial de modificaciones, accesos de familias, documentos emitidos | Cada uno carga, con filtros ciclo/unidad/sección |
| REP-02 | Descargar PDF de cada uno | TRV-12; columnas legibles; no se corta; datos coinciden con la pantalla |
| REP-03 | Filtros sin resultados | Mensaje "sin datos", PDF coherente |
| REP-04 | Métricas (2 porcentajes semanales) | Sin datos personales; números coherentes con la actividad real que hicieron |
| REP-05 | Quién accede | Dirección/Coord/Admin según matriz; Pagos no |

### Verificación pública por QR (RF-14, HU-14)

| ID | Caso | Esperado |
|---|---|---|
| QR-01 | Emitir un documento (set D) y abrir su QR/URL `/verificar/<código>` **sin sesión** | Muestra tipo, fecha y estudiante; sin datos sensibles |
| QR-02 | Código inventado / mal formado | "Documento no válido" amable |
| QR-03 | Sin sesión y con sesión de otro rol | Misma vista |

---

## SET B — Estudiantes, asignaciones, horarios y asistencia

### Estudiantes y encargados (RF-03, RF-04, RN-14, HU-03)

| ID | Caso | Esperado |
|---|---|---|
| EST-01 | Inscribir estudiante nuevo con datos del encargado | El **sistema** asigna código interno único; no se puede editar a mano |
| EST-02 | Inscribir dos veces al mismo estudiante en el mismo ciclo | Bloqueado con mensaje claro (HU-03); en otro ciclo sí |
| EST-03 | Campos obligatorios, fechas de nacimiento imposibles/futuras, nombres con tildes/ñ, espacios al inicio/fin | Validación |
| EST-04 | Buscar/filtrar/paginar con `seed_masivo` (~100+ estudiantes) | Rápido y correcto |
| EST-05 | Expediente: datos generales vs datos sensibles | Sensibles solo Dirección (editar) y Admin (ver) — PER-06 |
| EST-06 | Crear encargado con cuenta de familia en el mismo formulario | Se crea usuario + contraseña temporal; la familia puede entrar |
| EST-07 | Vincular un encargado a varios estudiantes y un estudiante a varios encargados; desvincular | Correcto; la familia ve solo sus vinculados (cruzar con D) |
| EST-08 | Editar/desactivar estudiante | No se borra; sale de listas activas, sigue en históricos |
| EST-09 | Encargado sin estudiantes, estudiante sin encargado | Se maneja sin romper |

### Asignaciones (RF-05, HU-05)

| ID | Caso | Esperado |
|---|---|---|
| ASG-01 | Asignar docente a curso+sección, maestro guía a sección, tallerista a taller | Selectores filtrados por tipo de sección/rol |
| ASG-02 | Asignar el mismo docente/curso dos veces; dos guías a una sección; curso sin docente | Reglas de HU-05 respetadas |
| ASG-03 | Reasignar/quitar una asignación que ya tiene notas/horarios/asistencia | No corrompe; mensaje claro |
| ASG-04 | Un docente solo ve lo suyo (operativo) | Alcance correcto |

### Horarios y calendario (RF-06, RF-22, RF-26, HU-06, RN-13, RN-17)

| ID | Caso | Esperado |
|---|---|---|
| HOR-01 | Grilla: 6 períodos de 40 min + receso | Estructura correcta |
| HOR-02 | Poner al mismo docente en dos secciones en el mismo período y día | Bloqueado (HU-06) con mensaje que diga dónde choca |
| HOR-03 | Poner dos cursos en el mismo período de la misma sección | Bloqueado |
| HOR-04 | Mover/editar/eliminar una clase | Se actualiza; se ve en "Mi horario" del docente y en el portal de familia (RF-26, RF-32) |
| HOR-05 | Coordinación y roles de solo ver | Sin controles de edición |
| CAL-01 | Calendario: Dirección crea aviso institucional y edita cualquier evento; docente crea/edita **solo los suyos** (RN-17) | Correcto; probar editar el de otro por URL/API |
| CAL-02 | Eventos con fecha pasada, rango invertido, solapados, todo el día | Validación |
| CAL-03 | Navegación semana/mes, hoy, cambio de mes en bordes (fin de año) | Correcto |
| CAL-04 | Calendario visible en portal de familia como primera pantalla (RF-28) | Coincide con lo publicado |

### Asistencia (RF-16, HU-16, RN-11, RN-12, RN-13)

| ID | Caso | Esperado |
|---|---|---|
| ASI-01 | Tomar asistencia de una sección: presente/tarde/ausente/justificado | Guarda; recarga y se mantiene |
| ASI-02 | **Corte 8:05**: llegada 7:59, 8:00, 8:05, 8:06, 8:40 | Hasta 8:05 presente; pasado de 8:05 = tarde y **pierde el primer período** (RN-11). Documentar exactamente el borde (8:05:00 vs 8:05:59) |
| ASI-03 | Modo "durante la clase" vs "al final de la jornada" (HU-16) | Ambos disponibles y consistentes |
| ASI-04 | Editar una asistencia ya guardada | Permitido según reglas, queda en bitácora (BIT-01) |
| ASI-05 | Fecha futura, fin de semana, día sin clases, fecha muy pasada | Validación o advertencia razonable |
| ASI-06 | Estudiante inscrito después / retirado | Aparece o no según corresponda |
| ASI-07 | Dirección registra la asistencia matutina | Puede, en el portal que le corresponda |
| ASI-08 | Docente solo toma asistencia de sus secciones; tallerista solo sus talleres | Alcance correcto (PER-05) |
| ASI-09 | Doble envío / dos usuarios tomando la misma asistencia a la vez | No duplica; última escritura clara |
| ASI-10 | Falta sin justificar | "Quita derecho a actividades del día" (RN-12): ver si el sistema lo refleja/indica |

### Justificaciones (RF-12)

| ID | Caso | Esperado |
|---|---|---|
| JUS-01 | Registrar justificación (tipo, fechas, motivo) para una falta | Queda pendiente |
| JUS-02 | **Solo Dirección** resuelve (aprobar/rechazar) | Otros roles no ven el botón ni por API |
| JUS-03 | Aprobada → la falta pasa a "justificado"; rechazada → sigue ausente | Reflejado en asistencia y en portal de familia |
| JUS-04 | Justificar días sin falta; rango que cruza ciclos; duplicar | Validación |

### Plantilla de asistencia de talleres (RF-21, HU-19/20)

| ID | Caso | Esperado |
|---|---|---|
| PLA-01 | Descargar plantilla del taller | Lista de participantes con código; estructura fija |
| PLA-02 | Cargar plantilla válida → vista previa → confirmar | Guarda |
| PLA-03 | Cargar con código alterado, columna borrada, valor inválido, archivo de otro tipo/vacío/enorme | Errores **por fila** claros en la vista previa; nada se guarda hasta confirmar |
| PLA-04 | Tallerista ve solo sus talleres | Alcance |
| PLA-05 | Asistencia de talleres aparece en el portal de familia (RF-31) | Sí |

---

## SET C — Notas y boletines (proceso central #1)

### Diseño de la unidad (RF-17, RN-04)

| ID | Caso | Esperado |
|---|---|---|
| NOT-01 | Definir actividades: 4 pruebas cortas de 10 pts + 60 pts distribuidos | Total en vivo; no pasa de 100 (RN-01/RN-02) |
| NOT-02 | Intentar superar 100; pesos 0, negativos, decimales, vacíos | Bloquea con mensaje claro |
| NOT-03 | Editar/eliminar una actividad que ya tiene punteos capturados | Advierte o bloquea; no deja notas huérfanas ni totales incoherentes |
| NOT-04 | Unidad ya cerrada (fecha de cierre pasada) | Diseño/captura restringidos según reglas |
| NOT-05 | Docente solo ve sus curso+sección; tallerista no tiene acceso a Notas | PER-05, matriz nota 5 |

### Captura (RF-18, RN-01, RN-02, RN-03, RN-05)

| ID | Caso | Esperado |
|---|---|---|
| NOT-06 | Capturar punteo por estudiante/actividad | Calcula nota de unidad; se guarda |
| NOT-07 | Límites: 0, 1, 100, 101, negativo, decimales (`7,5` y `7.5`), texto, vacío, mayor que el máximo de la actividad | Validación coherente |
| NOT-08 | Nota final del ciclo = promedio de las 4 unidades **redondeado sin decimales** | Probar casos de .5 (p. ej. 69.5, 59.5, 59.4): el criterio debe ser explícito y consistente en pantalla, boletín y reportes |
| NOT-09 | Aprobación con 60 (RN-03): 59, 59.5, 60 | Marca aprobado/reprobado bien |
| NOT-10 | Intentar **editar una nota ya registrada** directamente | No permite sobrescribir: ofrece "solicitar corrección" (RN-05) |
| NOT-11 | Estudiante sin nota en alguna actividad | Cómo se promedia (¿0? ¿vacío?) debe ser claro, nunca silencioso |
| NOT-12 | Volumen: sección de 10+ estudiantes con muchas actividades (`seed_masivo`) | Usable, sin lentitud, el foco/teclado Tab sirve para capturar rápido |

### Plantilla de calificaciones (RF-19, RF-20, HU-19, HU-20, RN-07)

| ID | Caso | Esperado |
|---|---|---|
| PLN-01 | Descargar plantilla por curso/sección/unidad | Estudiantes con código; estructura protegida |
| PLN-02 | Cargar plantilla correcta → vista previa → confirmar | Guarda y recalcula |
| PLN-03 | Códigos modificados, estudiantes faltantes/sobrantes, punteos inválidos o > máximo, columnas movidas, archivo equivocado/vacío/gigante | Errores **por fila** en la vista previa; nada se guarda sin confirmar |
| PLN-04 | **Plantilla cargada con la unidad cerrada** | Se trata como **solicitud de modificación** (RN-07), no sobrescribe |
| PLN-05 | Cargar la misma plantilla dos veces | No duplica ni corrompe |

### Modificaciones de nota (RF-23, RF-10, RN-05, RN-06)

| ID | Caso | Esperado |
|---|---|---|
| MOD-01 | Docente solicita corrección (nota propuesta + motivo obligatorio) | Queda pendiente; la nota vigente no cambia aún |
| MOD-02 | Dirección autoriza / rechaza (con motivo) | Al autorizar, la nota corregida entra a promedios; se conserva el punteo original (RN-05) |
| MOD-03 | Quedan registrados: original, propuesta, motivo, quién autorizó, cuándo | En la bandeja, bitácora y reporte de historial |
| MOD-04 | **La familia no ve el historial** (RN-06), solo la nota final | Verificar en portal Y por API |
| MOD-05 | El docente no puede autorizar sus propias solicitudes; Coordinación/otros no | Permisos |
| MOD-06 | Solicitar dos correcciones sobre la misma nota; resolver una ya resuelta | Manejo coherente |

### Boletines (RF-09, RF-34, RN-09, RN-10, RN-15)

| ID | Caso | Esperado |
|---|---|---|
| BOL-01 | Bandeja por sección/unidad: generar → aprobar → publicar (Borrador → Aprobado → Publicado) | Transiciones válidas; las inválidas dan mensaje claro |
| BOL-02 | **Estudiante insolvente** (hay en `seed_masivo`) | No se puede habilitar el boletín; el mensaje de RN-09 es comprensible |
| BOL-03 | Plazos: notas 15 días tras cierre; boletín 1 semana después de la entrega (RN-10) | Antes de plazo bloquea con la fecha exacta en el mensaje; después permite |
| BOL-04 | Combinaciones solvente/insolvente × plazo cumplido/no | Las dos condiciones se evalúan **juntas** |
| BOL-05 | PDF del boletín (formato institucional nuevo, cambios recientes en esta rama): logo, nombre, QR, notas por curso, promedio, firma del maestro guía **a mano (líneas en blanco)** | TRV-12; datos = pantalla; con y sin cursos reprobados; estudiante con curso sin notas |
| BOL-06 | Cambiar una nota (modificación aprobada) **después** de publicar el boletín | ¿Se regenera/avisa? Documentar el comportamiento |
| BOL-07 | Despublicar/revertir | Documentar si existe y si debería |
| BOL-08 | La familia descarga **solo** boletines publicados y solo de su hijo (cruzar con D) | Correcto |
| BOL-09 | **(K-2)** Describir como director: ¿dónde veo notas por sección/curso/estudiante? ¿dónde corrijo? ¿dónde veo el detalle de un boletín antes de aprobar? | Anotar qué ve hoy, qué esperaría y proponer la pantalla |
| BOL-10 | Roles sin acceso a Boletines | PER-02 |

---

## SET D — Pagos, documentos, comunicación y portal de familia

### Pagos y solvencia (RF-07, RF-08, HU-07, RN-08, RN-09)

| ID | Caso | Esperado |
|---|---|---|
| PAG-01 | Registrar pago: mes, fecha, monto, **número de recibo** | Se guarda; la solvencia se recalcula |
| PAG-02 | Recibo duplicado; mismo mes pagado dos veces; monto 0/negativo/con demasiados decimales; fecha futura; mes fuera del ciclo | Validación clara |
| PAG-03 | Estudiante **con beca** | Siempre solvente (RN-08), también con cero pagos |
| PAG-04 | Insolvente vs solvente: los estados y colores se entienden a simple vista; cálculo correcto del mes en curso | Correcto |
| PAG-05 | Corregir/anular un pago | Queda en bitácora (RNF-06); recalcula solvencia |
| PAG-06 | Solo Pagos y Dirección editan; Coordinación/Admin solo ven | PER-03 |
| PAG-07 | Botón de reporte de estudiantes insolventes (PDF) | Datos correctos; Pagos lo ve aunque no tenga Reportes |
| PAG-08 | Volumen con `seed_masivo` | Rápido, filtros útiles |

### Documentos (RF-08, RF-11, RF-14, HU-08, HU-11, RN-15)

| ID | Caso | Esperado |
|---|---|---|
| DOC-01 | Constancia de solvencia (Pagos/Dirección) | Solo a un estudiante solvente; PDF con nombre, logo, QR, sin firma digital |
| DOC-02 | Constancia de estudio, de buena conducta, carta membretada (Dirección) | Se emiten y descargan |
| DOC-03 | Bandeja "volver a descargar" | Reimprime sin duplicar la emisión (o la cuenta correctamente: RNF-07 cuenta documentos emitidos) |
| DOC-04 | **Pagos solo ve las constancias de solvencia que él emitió** | Alcance correcto |
| DOC-05 | Escanear/abrir el QR del PDF | Lleva a `/verificar/<código>` y valida (QR-01) |
| DOC-06 | Datos raros: nombre larguísimo, tildes, ñ, sin segundo apellido | El PDF no se rompe |
| DOC-07 | Documento para estudiante inactivo/retirado | Comportamiento razonable |

### Avisos (RF-13, RF-36, HU-36)

| ID | Caso | Esperado |
|---|---|---|
| AVI-01 | Dirección publica aviso a "todos" y a "una sección" | Solo lo ven los destinatarios (probar con familia de otra sección) |
| AVI-02 | Orden: más reciente primero; **vencidos dejan de mostrarse** | Correcto |
| AVI-03 | Fecha de vencimiento anterior a la de publicación, título/cuerpo vacíos o larguísimos | Validación |
| AVI-04 | Quién publica/ve (matriz: Coordinación `¿?`) | Documentar lo que ve hoy |

### Reportes de conducta (RF-24, RF-35)

| ID | Caso | Esperado |
|---|---|---|
| CON-01 | Maestro guía registra reporte **solo de su sección** (artículo del código de convivencia, descripción) | Correcto; no puede de otra sección (PER-05) |
| CON-02 | Dirección registra de cualquiera | Correcto |
| CON-03 | PDF del reporte (formato real del centro, actualizado en esta rama) | TRV-12 |
| CON-04 | Familia ve solo los de su hijo | Aislamiento |
| CON-05 | Docente sin sección a cargo usa los artículos del catálogo sin administrar el catálogo | Excepción de permisos funciona |

### Buzón (RF-25, RF-37, HU-25, HU-37, RN-16, RNF-10)

| ID | Caso | Esperado |
|---|---|---|
| BUZ-01 | Familia escribe; maestro guía de la sección y Dirección ven; **nadie más** (Coordinación, Pagos, otro docente, otra familia) | Visibilidad estricta |
| BUZ-02 | Respuesta en el **mismo hilo** | Correcto |
| BUZ-03 | Sin tiempo real, sin "escribiendo…", sin "visto" (HU-37) | No existen |
| BUZ-04 | Palabra inapropiada (el filtro es de lenguaje) | Mensaje rechazado, **bloqueo temporal** claro con hasta cuándo (RN-16, RNF-10); después del bloqueo puede volver (probar con el corrector ajustando el tiempo o con test) |
| BUZ-05 | Falsos positivos: palabras normales con tildes/mayúsculas/dentro de otra palabra (efecto "Scunthorpe") | No bloquea mensajes legítimos |
| BUZ-06 | Mensaje vacío, larguísimo, con emojis/HTML (`<script>`) | Sin romper; HTML se muestra como texto |
| BUZ-07 | Familia con hijos en secciones distintas | Cada hilo llega al guía correcto |

> ⚠️ BUZ-04 bloquea `familia.demo` 24 h en tu base local. Hazlo al final o resetea la base (`rm db.sqlite3 && migrate && seed_demo`).

### Portal de familia (RF-27 a RF-37, RNF-01, RNF-04) — **probar en celular o 375 px**

| ID | Caso | Esperado |
|---|---|---|
| POR-01 | Login familia; cuenta con 2+ estudiantes: selector de estudiante (HU-27) | Cambia sin cerrar sesión; toda la información cambia con él |
| POR-02 | Primera pantalla = calendario semanal con el horario del estudiante (RF-28, RF-32) | Correcto |
| POR-03 | Notas por curso y unidad: **solo la nota final**, sin historial (RN-06) | Correcto; revisar pestaña Network: la respuesta de la API **tampoco** trae `raw_score` ni historial |
| POR-04 | Puntos que faltan para aprobar (RF-30) | K-3: solo confirmar que no hay nada roto |
| POR-05 | Asistencia y faltas, incluidos talleres (RF-31) | Coincide con lo registrado en Set B |
| POR-06 | Pagos y descarga de constancia de solvencia (RF-33) | Solo si está solvente/habilitado |
| POR-07 | Boletín: solo se ve/descarga **cuando está publicado** y cumple RN-09/RN-10 (RF-34) | Antes: mensaje claro de por qué no |
| POR-08 | Reportes de conducta del estudiante (RF-35) | Solo los suyos |
| POR-09 | Cartelera de avisos (RF-36) | Orden y vigencia correctos |
| POR-10 | Buzón (RF-37) | BUZ-* desde el lado familia |
| POR-11 | Página de Convivencia (manual de convivencia, nueva en esta rama) | Contenido legible, navegable en móvil, fiel al manual (`formatos_institucionales/`) |
| POR-12 | **Aislamiento (RNF-04, crítico)**: con DevTools, tomar un request del portal y cambiar el `publicId` del estudiante por el de un alumno **no vinculado** (créalo con otro encargado) | 403/404, jamás datos |
| POR-13 | Familia intenta abrir pantallas administrativas/operativas por URL | Redirige/niega |
| POR-14 | Lenguaje sencillo y tono institucional; sin jerga técnica (RNF-08); tabs inferiores y encabezado usables con una mano | Correcto |
| POR-15 | Un estudiante sin notas/pagos/asistencia aún | Estados vacíos amables, no errores |
