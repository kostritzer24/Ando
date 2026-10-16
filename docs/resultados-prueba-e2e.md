# Informe de prueba e2e (15/10/2026)
Completados: 95/115 · Fallos anotados: 23

## Fallos
- [Nivel 2] Entra como coord.demo (otra ventana) y revisa Datos maestros
  Esperado: Puede VER pero no hay botones de crear/editar/borrar.
  Pasó: En la vista de coord.demo intente entrar en datos maestros>seccoines y me tira que no esta disponible en este momento y este mensaje en consola "resource.ts:45 
 GET http://localhost:8000/api/v1/users/?page_size=200 403 (Forbidden)
Promise.then		
(anonymous)	@	resource.ts:45
(anonymous)	@	catalogoApi.ts:36
cargar	@	SeccionesPage.vue:69
" 
- [Nivel 3] Estudiantes → Inscribir. Crea «Pedro Ajú Chávez», nacido el 3/3/2012, sección Segundo básico
  Esperado: Se crea con código interno único. Aparece en la lista.
  Pasó: Sección y Beca aparecen solo con opción "Ninguna"
Al no poder seleccionar seccion no deja inscribir al alumno.
Al hacer refresh de la página ya funcionó todo.
Al terminar si lanzó el mensaje "Estudiante inscrito con el código ES005."

Mas adelante en la prueba cuando quise agregar otor usuario siempre que regreso a esta pestaña aparece como que no es valido y no tengo permiso, pero al recargar ya funciona.

En la seleccion de secciones no hay forma de diferenciar las secciones de los distintos años.
- [Nivel 3] Vincula a Rosa con Pedro (parentesco Madre, principal)
  Esperado: El vínculo aparece; «Ver vínculos» muestra la relación.
  Pasó: Si funciona pero para todos estos campos donde se debe seleccionar a alguien seria mejor un campo escrito con prediccion en vez de un select que se hace gigante. 
- [Nivel 3] En el cambio de contraseña, usa la MISMA contraseña provisional
  Esperado: Se rechaza (debe ser distinta).
  Pasó: Dejo usar la misma contraseña provicional como contraseña fija
- [Nivel 4] Intenta poner OTRO curso en ese mismo día y período para la misma sección
  Esperado: Se rechaza por cruce, con motivo.
  Pasó: Aveces funciona el detector de cruces y aveces no, debe mejorarse, cuando docente 1 se le pusieron sus clases ( lenguaje y naturales ) en segundo basicio lunes periodo 1 y 2 todo bien, luego con docente 2 se creo su usuario y se le asigno sociales en segundo basico y ponerlo lunes primer periodo no dio ninguna error, al regresar a docente 1 y quitar sus cursos y tratar de volver a colcoarlso solo naturales dio error, al colocar lenguaje funciono y dejo duplicar los periodos. Tambien agregar la funcionalidad de exportar en pdf los horarios establecidos por persona y por grado. Hacer el proceso mas facil dejando ver que casillas estan disponibles y cuales no, automatizar mas el proceso.
- [Nivel 5] Registra una justificación para el ausente (tipo Motivo familiar)
  Esperado: Queda «pendiente».
  Pasó: No veo donde se registra esto, no sale nada y el espadio al lado solo es un cuadrado blanco que no hace nada. Ahora si voy a la pestaña de justificaciones no me deja elejir nada en la primera opción "Falta a justificar" todo lo demás si deja llenarlo pero la primera opción solo sale "Elejir una opción"
- [Nivel 5] Intenta registrar otra justificación para la misma falta
  Esperado: Se rechaza por repetida.
  Pasó: No puedo registrar justificacoines
- [Nivel 5] Como dir.demo → Justificaciones: resuelve la pendiente
  Esperado: Solo Dirección resuelve. Al intentar resolverla de nuevo, no se deja.
  Pasó: No sale ninguna pero es porque no puedo registrar ninguna.
- [Nivel 5] Como tallerista.demo → Asistencia del taller de panadería
  Esperado: La asistencia del taller es aparte de la de la mañana (solo ve su taller).
  Pasó: Me deja colocar asistencia de cualquier taller no solo del mio.
- [Nivel 7] Pagos y solvencia → elige a María Ximena Pérez
  Esperado: «Al día con sus pagos». El botón de constancia está activo.
  Pasó: María Ximena Perez aparece 2 veces, y una version esta full con pagos y la otra no. No se si esto tenga que ver con su registro a un grado y a un taller.
- [Nivel 7] Registra un pago de enero 2026 por Q150.00 con recibo «PRUEBA-001»
  Esperado: Aparece en la tabla de pagos, con fecha legible (dd/mm/aaaa) y monto en Q.
  Pasó: Si paso todo bien pero el no. de recibo debe ser automatico no manual. El sistema de busqueda en esta seccion esta bastante bien no creo que requiera cambios.
- [Nivel 8] Dirección → Documentos → emite una Constancia de estudio de María Ximena
  Esperado: Se descarga el PDF y aparece en la bandeja de documentos emitidos.
  Pasó: El mismo caso con el registrar nuevo estudiante al entrar da error y al actualizar ya funciona
- [Nivel 8] Descarga otra vez un documento desde la bandeja
  Esperado: El archivo tiene un nombre claro (tipo + estudiante).
  Pasó: Si dejo descargar otra vez pero no tiene el nombre tipo+estudiante en vez de eso tiene 06719BACA5A4.pdf
- [Nivel 8] Entra como pagos.demo → Documentos
  Esperado: NO ve el formulario de emitir; solo ve constancias de solvencia.
  Pasó: El mismo caso con el usuario de direccoin nuevo estudiante al entrar da error y al actualizar ya funciona
- [Nivel 9] Boletines → Segundo básico · Unidad 1 → Generar
  Esperado: Se crean los boletines en «Borrador».
  Pasó: El mismo caso marca error cuando entro pero al recargar ya funciona. 
- [Nivel 10] Entra como familia.demo → Avisos
  Esperado: Ve el aviso de todos y el de Segundo básico (sus hijos están ahí).
  Pasó: Si funcinan pero me gustaria que los avisos sean visiblemente mas llamativos porque se mira demasiado blanca la parte de anuncios.
- [Nivel 10] Como guia.demo → Reportes de conducta: registra uno a un estudiante de TU sección con un artículo del código
  Esperado: Se guarda y puedes descargar el PDF con el formato del centro.
  Pasó: Esta bien pero no me gusta que exita el rol y el usuario de guia, esto es porque cualquier docente puede ser maestro guia de una seccion por lo que no tiene sentido crear usuarios de docentes y de guias, mejor solo dejar docentes y matar guias es decir darle a los docentes la habilidad de levantar reportes.
- [Nivel 11] Asistencia
  Esperado: Muestra la mañana y también el taller, por separado.
  Pasó: Si deja registrar la asitencia y si se muestra en la plataforma de los padres, lo que no me gusta es que estaba viendo como agregar a un estudiante a un taller para podre marcar su asistencia pero segun veo para hacerlo necesito registrar nuevamente el estudiante pero esta vez en seccoin le pongo la seccion del taller y eso se me hace tonto en el expediente del estudiante debo poder tener la habilidad de inscribirlo a un taller o sacarlo de uno al igual que actualizar el grado/seccion en el que se encuentra no crear uno nuevo y creo que de aqui salen lo del os estudiantes dulpicados cuando si esta en un taller.
- [Nivel 12] Familia → Buzón: escribe un mensaje normal a la sección de Segundo básico
  Esperado: Se envía y aparece en el hilo.
  Pasó: Si funciona pero tiene varios detalles: primero al mandar una palabra muy larga se alarga la pantalla de la vista movil y se arruina por completo, se crea scroll horizontal mientras que del lado de ambos paneles tambien se vuelve confuso el manejar tantos mensajes por la visual tan blanca da otra propuesta para que la visual mejore en este sentido.
- [Nivel 12] Intenta responder como docente.demo (sin ser maestro guía)
  Esperado: No puedes: solo el guía de la sección o Dirección.
  Pasó: Mismo caso que anterior, docentes deberian poder responder. Y la respuesta deberia indicar quien fue el que respondio sea docente o direccion.
- [Nivel 13] dir.demo → Reportes: abre los 8 reportes uno por uno
  Esperado: Cada uno carga, filtra por ciclo/sección/unidad y baja en PDF correcto.
  Pasó: Aca encontre la forma de generar el horario asi general pero no sirve que sea en liista debe de ser de modo cuadricula. 
- [Jefe final] Repite lo esencial en vista móvil (375 px)
  Esperado: Anota lo que se vea apretado o cortado.
  Pasó: Los mensajes del buzon y textos largos se salen de la vista y la alargan rompiendola
- [Jefe final] Revisa que no haya ningún texto en inglés, «undefined», «null» ni IDs largos a la vista
  Esperado: Todo en español y con tono neutro.
  Pasó: (sin nota)


Encuentros adicionales encontrados por los demas companeros:
Los pagos deben de estar limitados ciclo basico 100 cilo bachillerato 150
Secciones duplicadas no las detecta, se puede colocar infnitos Quintos Bachilleratos A por ejemplo
Deja colocar fechas tontas como 1800 para edades.
No se pueden colocar horarios de talleres.
Concuerdan en elminar a doncente guia y dejar solo docente
Eliminar el rol admin tambien ya que no sirve que solo se vean datos
Eliminar becas parciales. 
En tipo de beca puede ser solamente completa o ninguna.
aun hay mensajes de error en ingles al duplicar un maestro, "Cuando se crea un duplicado de asignación de docente el mensaje aparece: Los campos teacher, course, section, cycle deben formar un conjunto único."

Todos probamos en conjunto el apartado de justificacoines, lo que era esra que estab marcando a los estudiantes como justificados, no sabia que habia que marcarlos como ausentes para poder subirles una justificaciones, se probo ahora si la funcionalidad de subir el archivo para luego descargarlo y si funciono, excepto en la compu de un amigo, funicono en 4 computadoras, en solo 1 comenzo a descargar los archivos sin formato solo como archivo en blanco y ninguna app lo puede abrir. Asi que ignora lo mencionado de justificacion que no lo pude probar antes.


