"""
Comando de siembra de demostración: parte de `seed_fase3` (roles y
usuarios de prueba) y agrega datos maestros reales — un ciclo escolar con
sus 4 unidades, las 6 secciones de la jornada matutina más una de taller
(sección 1 del prompt maestro), cursos, catálogos y los artículos del
código de convivencia de `docs/reporte.docx` (ADR-0006) — más un puñado
de estudiantes, encargados y asignaciones docentes para poder mostrar
flujos completos.

Es el mismo comando que se sigue extendiendo fase a fase hasta llegar al
"sistema listo para demostración" de la sección 16 del prompt maestro —
no se crea un comando nuevo por cada fase. Vive en `core` (no en
`catalog`) porque de acá en adelante toca varias apps a la vez.
"""

from datetime import date
from decimal import Decimal

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.catalog.models import (
    ActivityType,
    ConductRuleArticle,
    Course,
    DocumentType,
    JustificationType,
    Scholarship,
    SchoolCycle,
    Section,
)
from apps.catalog.services.grading_unit import crear_unidad
from apps.catalog.services.section import crear_seccion
from apps.payments.domain.solvency import meses_del_periodo
from apps.payments.models import Payment
from apps.payments.services.payment import registrar_pago
from apps.scheduling.domain.teacher_assignment import AsignacionInvalida
from apps.scheduling.models import TeacherAssignment
from apps.scheduling.services.teacher_assignment import crear_asignacion
from apps.students.models import Enrollment, Student
from apps.students.services.enrollment import YaInscritoEnEsaSeccion, inscribir_estudiante
from apps.students.services.guardian import crear_encargado
from apps.students.services.link import VinculoYaExiste, vincular_encargado_estudiante
from apps.students.services.student import crear_estudiante

_SECCIONES = [
    ("Primero básico", "A", Section.TIPO_ACADEMICA),
    ("Primero básico", "B", Section.TIPO_ACADEMICA),
    ("Segundo básico", "", Section.TIPO_ACADEMICA),
    ("Tercero básico", "", Section.TIPO_ACADEMICA),
    ("Cuarto bachillerato", "", Section.TIPO_ACADEMICA),
    ("Quinto bachillerato", "", Section.TIPO_ACADEMICA),
    ("Taller de panadería", "", Section.TIPO_TALLER),
]

_CURSOS = [
    ("Matemática", Course.TIPO_ACADEMICO),
    ("Comunicación y lenguaje L1", Course.TIPO_ACADEMICO),
    ("Ciencias naturales", Course.TIPO_ACADEMICO),
    ("Ciencias sociales", Course.TIPO_ACADEMICO),
    ("Idioma extranjero — inglés", Course.TIPO_ACADEMICO),
    ("Formación ciudadana", Course.TIPO_ACADEMICO),
    ("Educación física", Course.TIPO_ACADEMICO),
    ("Expresión artística", Course.TIPO_ACADEMICO),
    ("Panadería", Course.TIPO_TALLER),
]

_TIPOS_ACTIVIDAD = [
    ("Prueba corta", True),
    ("Tarea", False),
    ("Proyecto", False),
    ("Examen de unidad", False),
]

_TIPOS_JUSTIFICACION = [
    ("Constancia médica", True),
    ("Motivo familiar", False),
    ("Cita médica o control", True),
]

_TIPOS_DOCUMENTO = [
    ("Constancia de solvencia", "constancia_solvencia"),
    ("Constancia de estudio", "constancia_estudio"),
    ("Constancia de buena conducta", "constancia_conducta"),
    ("Carta membretada", "carta_membretada"),
]

_BECAS = [
    ("Beca completa", "Cubre el 100 % de la mensualidad."),
    ("Beca parcial", "Cubre el 50 % de la mensualidad."),
]

# Del formato real docs/reporte.docx (ADR-0006). Dos incisos comparten a
# propósito el mismo número de artículo (Art. 2 y Art. 8): así está en el
# documento original, no es un error de captura.
_ARTICULOS_CONDUCTA = [
    ("CAPÍTULO I: RESPETO Y DIGNIDAD", "Art. 1", "Toma no autorizada de pertenencias"),
    ("CAPÍTULO I: RESPETO Y DIGNIDAD", "Art. 2", "Actos de discriminación u hostigamiento"),
    ("CAPÍTULO I: RESPETO Y DIGNIDAD", "Art. 2", "Uso de lenguaje o símbolos de odio"),
    ("CAPÍTULO I: RESPETO Y DIGNIDAD", "Art. 3", "Demostraciones de afecto inapropiadas"),
    ("CAPÍTULO I: RESPETO Y DIGNIDAD", "Art. 4", "Falta de respeto hacia educadores"),
    ("CAPÍTULO II: SEGURIDAD Y SALUD", "Art. 5", "Sustancias u objetos peligrosos"),
    ("CAPÍTULO II: SEGURIDAD Y SALUD", "Art. 6", "Contenido inapropiado"),
    ("CAPÍTULO III: USO DE TECNOLOGÍA", "Art. 7", "Uso no autorizado de dispositivos"),
    ("CAPÍTULO III: USO DE TECNOLOGÍA", "Art. 8", "Fotos/grabaciones sin consentimiento"),
    ("CAPÍTULO III: USO DE TECNOLOGÍA", "Art. 8", "Ciberacoso o difamación"),
    ("CAPÍTULO IV: RESPONSABILIDAD ACADÉMICA", "Art. 9", "Puntualidad o asistencia"),
    ("CAPÍTULO IV: RESPONSABILIDAD ACADÉMICA", "Art. 10", "Copia o plagio"),
    ("CAPÍTULO IV: RESPONSABILIDAD ACADÉMICA", "Art. 11", "Uso indebido del tiempo de clase"),
    ("CAPÍTULO V: CUIDADO DEL ENTORNO", "Art. 12", "Daño a mobiliario o instalaciones"),
    ("CAPÍTULO V: CUIDADO DEL ENTORNO", "Art. 13", "Falta de higiene y limpieza"),
    ("CAPÍTULO V: CUIDADO DEL ENTORNO", "Art. 14", "Conducta inapropiada en áreas comunes"),
]

# (nombres, fecha de nacimiento, sección donde se inscribe)
_ESTUDIANTES = [
    ("María Ximena", "Pérez Tzul", date(2013, 5, 14), "Segundo básico", ""),
    ("Juan Carlos", "López Xitumul", date(2012, 8, 2), "Segundo básico", ""),
    ("Ana Lucía", "Con Morales", date(2011, 11, 20), "Tercero básico", ""),
    ("Diego Alejandro", "Ramírez Cabrera", date(2010, 2, 9), "Primero básico", "A"),
]


class Command(BaseCommand):
    help = "Siembra de demostración: roles, usuarios, datos maestros, expedientes y asignaciones."

    @transaction.atomic
    def handle(self, *args, **options):
        call_command("seed_fase3")

        ciclo, creado = SchoolCycle.objects.get_or_create(
            year=2026,
            defaults={
                # Objetos date(...) reales, no texto: el objeto que
                # devuelve get_or_create() se sigue usando en memoria el
                # resto del comando (más abajo, en _sembrar_pagos, se le
                # hace aritmética de fechas) — un `str` ahí revienta
                # aunque Django lo hubiera guardado bien en la base.
                "start_date": date(2026, 1, 12),
                "end_date": date(2026, 10, 30),
                "status": SchoolCycle.ESTADO_ACTIVO,
            },
        )
        self.stdout.write(("Creado" if creado else "Ya existía") + f" el ciclo {ciclo.year}")

        if not ciclo.units.exists():
            rangos = [
                (date(2026, 1, 12), date(2026, 2, 28)),
                (date(2026, 3, 2), date(2026, 4, 24)),
                (date(2026, 4, 27), date(2026, 6, 19)),
                (date(2026, 6, 22), date(2026, 8, 14)),
            ]
            for numero, (inicio, cierre) in enumerate(rangos, start=1):
                crear_unidad(cycle=ciclo, number=numero, start_date=inicio, end_date=cierre)
            self.stdout.write(
                "Creadas las 4 unidades del ciclo, con sus fechas calculadas (RN-10)."
            )

        maestro_guia = User.objects.filter(username="guia.demo").first()
        for indice, (grade, letter, tipo) in enumerate(_SECCIONES):
            if Section.objects.filter(cycle=ciclo, grade=grade, letter=letter).exists():
                continue
            homeroom_teacher = maestro_guia if indice == 0 else None
            crear_seccion(
                cycle=ciclo,
                grade=grade,
                letter=letter,
                type=tipo,
                homeroom_teacher=homeroom_teacher,
            )
        self.stdout.write(f"Secciones listas ({Section.objects.filter(cycle=ciclo).count()}).")

        for name, tipo in _CURSOS:
            Course.objects.get_or_create(name=name, defaults={"type": tipo})

        for name, es_prueba_corta in _TIPOS_ACTIVIDAD:
            ActivityType.objects.get_or_create(
                name=name, defaults={"counts_as_short_quiz": es_prueba_corta}
            )

        for name, requiere_documento in _TIPOS_JUSTIFICACION:
            JustificationType.objects.get_or_create(
                name=name, defaults={"requires_document": requiere_documento}
            )

        for name, template_key in _TIPOS_DOCUMENTO:
            DocumentType.objects.get_or_create(name=name, defaults={"template_key": template_key})

        for name, description in _BECAS:
            Scholarship.objects.get_or_create(name=name, defaults={"description": description})

        for chapter, code, description in _ARTICULOS_CONDUCTA:
            ConductRuleArticle.objects.get_or_create(
                chapter=chapter, code=code, description=description
            )

        self._sembrar_expedientes_y_asignaciones(ciclo)
        self._sembrar_pagos(ciclo)

        self.stdout.write(self.style.SUCCESS("Siembra de demostración lista (fases 3 a 9)."))

    def _sembrar_expedientes_y_asignaciones(self, ciclo):
        if not Student.objects.exists():
            for first_name, last_name, birth_date, grade, letter in _ESTUDIANTES:
                estudiante = crear_estudiante(
                    first_name=first_name, last_name=last_name, birth_date=birth_date
                )
                seccion = Section.objects.get(cycle=ciclo, grade=grade, letter=letter)
                try:
                    inscribir_estudiante(
                        student=estudiante,
                        section=seccion,
                        cycle=ciclo,
                        enrolled_at=ciclo.start_date,
                    )
                except YaInscritoEnEsaSeccion:
                    pass
            self.stdout.write(f"Estudiantes inscritos ({Student.objects.count()}).")

            # Un mismo estudiante también puede estar en un taller de la
            # tarde (sección 1 del prompt maestro): demuestra que ya no
            # está limitado a una sola inscripción por ciclo.
            primer_estudiante = Student.objects.order_by("internal_code").first()
            seccion_taller = Section.objects.filter(cycle=ciclo, type=Section.TIPO_TALLER).first()
            if primer_estudiante and seccion_taller:
                try:
                    inscribir_estudiante(
                        student=primer_estudiante,
                        section=seccion_taller,
                        cycle=ciclo,
                        enrolled_at=ciclo.start_date,
                    )
                    self.stdout.write(f"{primer_estudiante} también inscrito en el taller.")
                except YaInscritoEnEsaSeccion:
                    pass

        usuario_familia = User.objects.filter(username="familia.demo").first()
        if usuario_familia and not hasattr(usuario_familia, "guardian"):
            encargada = crear_encargado(user=usuario_familia, full_name="Encargada Demo")
            # Dos hijos, no uno: la sección 16 del prompt maestro pide el
            # flujo de extremo a punta "consultar el portal como encargado
            # con dos hijos" (HU-27, selector entre estudiantes vinculados).
            for estudiante in Student.objects.order_by("internal_code")[:2]:
                try:
                    vincular_encargado_estudiante(
                        guardian=encargada,
                        student=estudiante,
                        relationship="Madre",
                        is_primary=(estudiante == Student.objects.order_by("internal_code").first()),
                    )
                except VinculoYaExiste:
                    pass
                self.stdout.write(f"Encargada vinculada a {estudiante}.")

        docente = User.objects.filter(username="docente.demo").first()
        matematica = Course.objects.filter(name="Matemática").first()
        segundo_basico = Section.objects.filter(
            cycle=ciclo, grade="Segundo básico", type=Section.TIPO_ACADEMICA
        ).first()
        if (
            docente
            and matematica
            and segundo_basico
            and not TeacherAssignment.objects.filter(
                teacher=docente, course=matematica, section=segundo_basico, cycle=ciclo
            ).exists()
        ):
            try:
                crear_asignacion(
                    teacher=docente, course=matematica, section=segundo_basico, cycle=ciclo
                )
                self.stdout.write("Docente de demostración asignado a Matemática, Segundo básico.")
            except AsignacionInvalida:
                pass

        # El maestro guía también da un curso a su propia sección — no solo
        # firma boletines y reportes de conducta (sección 2 del prompt
        # maestro): sin una TeacherAssignment propia no llega ni a la lista
        # de sus propios estudiantes (RF-24), porque ese alcance se filtra
        # siempre por asignación docente, nunca por `homeroom_teacher`.
        guia = User.objects.filter(username="guia.demo").first()
        comunicacion = Course.objects.filter(name="Comunicación y lenguaje L1").first()
        primero_basico_a = Section.objects.filter(
            cycle=ciclo, grade="Primero básico", letter="A", type=Section.TIPO_ACADEMICA
        ).first()
        if (
            guia
            and comunicacion
            and primero_basico_a
            and not TeacherAssignment.objects.filter(
                teacher=guia, course=comunicacion, section=primero_basico_a, cycle=ciclo
            ).exists()
        ):
            try:
                crear_asignacion(
                    teacher=guia, course=comunicacion, section=primero_basico_a, cycle=ciclo
                )
                self.stdout.write("Maestro guía de demostración asignado a su propia sección.")
            except AsignacionInvalida:
                pass

        tallerista = User.objects.filter(username="tallerista.demo").first()
        panaderia = Course.objects.filter(name="Panadería").first()
        seccion_taller = Section.objects.filter(cycle=ciclo, type=Section.TIPO_TALLER).first()
        if (
            tallerista
            and panaderia
            and seccion_taller
            and not TeacherAssignment.objects.filter(
                teacher=tallerista, course=panaderia, section=seccion_taller, cycle=ciclo
            ).exists()
        ):
            try:
                crear_asignacion(
                    teacher=tallerista, course=panaderia, section=seccion_taller, cycle=ciclo
                )
                self.stdout.write("Tallerista de demostración asignado al taller de panadería.")
            except AsignacionInvalida:
                pass

    def _sembrar_pagos(self, ciclo):
        """RF-07/RN-08, sección 16: deja el sistema con una mezcla real de
        estudiantes solventes e insolventes para poder demostrar la
        constancia de solvencia (RF-08) en ambos casos sin tener que
        registrar pagos a mano antes de la demo."""
        if Payment.objects.exists():
            return
        usuario_pagos = User.objects.filter(username="pagos.demo").first()
        estudiantes = list(Student.objects.order_by("internal_code")[:4])
        if not usuario_pagos or len(estudiantes) < 4:
            return

        def _inscripcion_academica(estudiante):
            return Enrollment.objects.filter(
                student=estudiante, cycle=ciclo, section__type=Section.TIPO_ACADEMICA
            ).first()

        solvente, becada, insolvente, parcial = (_inscripcion_academica(e) for e in estudiantes)

        beca = Scholarship.objects.filter(name="Beca completa").first()
        if becada and beca and becada.scholarship_id is None:
            becada.scholarship = beca
            becada.save(update_fields=["scholarship"])

        hoy = timezone.localdate()
        meses = sorted(meses_del_periodo(inicio=ciclo.start_date, hasta=min(hoy, ciclo.end_date)))

        def _pagar(inscripcion, meses_a_pagar):
            for anio, mes in meses_a_pagar:
                receipt = f"DEMO-{inscripcion.student.internal_code}-{anio}{mes:02d}"
                if Payment.objects.filter(receipt_number=receipt).exists():
                    continue
                registrar_pago(
                    enrollment=inscripcion,
                    period_month=mes,
                    period_year=anio,
                    amount=Decimal("150.00"),
                    payment_date=date(anio, mes, 1),
                    receipt_number=receipt,
                    recorded_by=usuario_pagos,
                )

        if solvente:
            _pagar(solvente, meses)  # al día con todos los meses transcurridos.
        if parcial and len(meses) > 1:
            _pagar(parcial, meses[:-1])  # le falta el mes más reciente: insolvente.
        # `insolvente` se queda sin ningún pago a propósito.
        # `becada` no necesita pagos: la beca la deja solvente igual (RN-08).

        self.stdout.write(
            "Pagos de demostración listos: un estudiante solvente, uno becado, "
            "uno sin pagos y uno con un mes pendiente."
        )
