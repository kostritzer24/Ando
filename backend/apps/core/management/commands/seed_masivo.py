"""
Siembra masiva para probar el sistema a fondo, sobre todo el flujo de
boletines (RF-09, RN-09, RN-10): parte de `seed_demo` y le suma ~10
estudiantes por sección académica, todos los cursos asignados a todas las
secciones, actividades y notas de las unidades 1 a 3, pagos con distintos
perfiles de solvencia, asistencia reciente, justificaciones, solicitudes
de cambio de nota y boletines en los tres estados.

Cada etapa se salta si ya hay datos suyos, así que volver a correrlo no
duplica nada. Es determinista (semilla fija) para que dos bases
reconstruidas den los mismos casos.
"""

import random
from datetime import date, timedelta
from decimal import Decimal

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import Role, User
from apps.attendance.models import Attendance
from apps.attendance.services.justification import crear_justificacion, resolver_justificacion
from apps.catalog.models import (
    ActivityType,
    Course,
    GradingUnit,
    JustificationType,
    Scholarship,
    SchoolCycle,
    Section,
)
from apps.grading.domain.report_card import TransicionDeBoletinInvalida
from apps.grading.models import Activity, Grade, ReportCard
from apps.grading.services.activity import crear_actividad
from apps.grading.services.grade import registrar_punteo
from apps.grading.services.grade_change_request import (
    resolver_modificacion,
    solicitar_modificacion,
)
from apps.grading.services.report_card import aprobar_boletin, generar_boletines, publicar_boletin
from apps.payments.domain.solvency import meses_del_periodo
from apps.payments.models import Payment
from apps.payments.services.payment import registrar_pago
from apps.scheduling.models import TeacherAssignment
from apps.scheduling.services.teacher_assignment import crear_asignacion
from apps.students.models import Enrollment, Student
from apps.students.services.enrollment import inscribir_estudiante
from apps.students.services.guardian import crear_encargado
from apps.students.services.link import vincular_encargado_estudiante
from apps.students.services.student import crear_estudiante

_CONTRASENA = "CambiaEstaClave2026"
_POR_SECCION = 10
_UNIDADES_CON_NOTAS = (1, 2, 3)

_NOMBRES = [
    "Sofía", "Mateo", "Valentina", "Santiago", "Camila", "Sebastián", "Isabella", "Emiliano",
    "Daniela", "Gabriel", "Luciana", "Nicolás", "Mariana", "Joaquín", "Renata", "Samuel",
    "Andrea", "Julián", "Paula", "Adrián", "Karla", "Bryan", "Heidy", "Kevin", "Rosa",
    "Elías", "Brenda", "Josué", "Mishel", "Axel",
]  # fmt: skip
_APELLIDOS = [
    "García", "Hernández", "López", "Martínez", "González", "Pérez", "Rodríguez", "Sánchez",
    "Ramírez", "Cruz", "Gómez", "Morales", "Tzul", "Xitumul", "Ixcoy", "Cumes", "Choc",
    "Batz", "Coc", "Tuyuc", "Mendoza", "Castillo", "Ortiz", "Vásquez", "Reyes", "Cojtí",
]  # fmt: skip

# Edad aproximada por grado, para fechas de nacimiento creíbles.
_EDAD_POR_GRADO = {
    "Primero básico": 13,
    "Segundo básico": 14,
    "Tercero básico": 15,
    "Cuarto bachillerato": 16,
    "Quinto bachillerato": 17,
}

# Perfil de rendimiento -> (peso, fracción media del punteo máximo, ruido).
# Da una mezcla de aprobados holgados, justos y reprobados en cada boletín.
_PERFILES = {
    "sobresaliente": (0.25, 0.92, 0.05),
    "promedio": (0.40, 0.76, 0.08),
    "justo": (0.20, 0.63, 0.07),
    "reprobado": (0.15, 0.42, 0.10),
}

# (tipo de actividad, nombre, punteo máximo): 4 pruebas cortas + resto = 100.
_DISENO_UNIDAD = [
    ("Prueba corta", "Prueba corta 1", 10),
    ("Prueba corta", "Prueba corta 2", 10),
    ("Prueba corta", "Prueba corta 3", 10),
    ("Prueba corta", "Prueba corta 4", 10),
    ("Tarea", "Tarea de la unidad", 20),
    ("Proyecto", "Proyecto de la unidad", 15),
    ("Examen de unidad", "Examen de unidad", 25),
]

# Perfil de pago -> peso. "al_dia" paga todo; "atrasado" solo los primeros 2
# meses (solvente para la unidad 1, no para las siguientes); "moroso" nada.
_PERFILES_PAGO = {"al_dia": 0.60, "atrasado": 0.20, "moroso": 0.15, "becado": 0.05}


def _elegir(rng: random.Random, pesos: dict):
    return rng.choices(
        list(pesos), weights=[p[0] if isinstance(p, tuple) else p for p in pesos.values()]
    )[0]


class Command(BaseCommand):
    help = "Siembra masiva (estudiantes, notas, pagos, asistencia y boletines) sobre seed_demo."

    @transaction.atomic
    def handle(self, *args, **options):
        call_command("seed_demo", stdout=self.stdout)
        self.rng = random.Random(2026)
        self.ciclo = SchoolCycle.objects.get(year=2026)
        self.unidades = {u.number: u for u in GradingUnit.objects.filter(cycle=self.ciclo)}
        self.docentes_demo = {
            "pagos": User.objects.get(username="pagos.demo"),
            "dir": User.objects.get(username="dir.demo"),
            "docente": User.objects.get(username="docente.demo"),
        }

        self._sembrar_docentes_y_asignaciones()
        self._sembrar_estudiantes()
        self._sembrar_pagos()
        self._sembrar_actividades_y_notas()
        self._sembrar_asistencia()
        self._sembrar_cambios_de_nota()
        self._sembrar_boletines()

        self.stdout.write(self.style.SUCCESS("Siembra masiva lista."))
        self.stdout.write(
            f"  estudiantes: {Student.objects.count()} · notas: {Grade.objects.count()} · "
            f"pagos: {Payment.objects.count()} · boletines: {ReportCard.objects.count()}"
        )
        self.stdout.write(f"  usuarios nuevos: docente.01..06 y familia.01.. (clave {_CONTRASENA})")

    # -- docentes y asignaciones -------------------------------------------------

    def _sembrar_docentes_y_asignaciones(self):
        rol = Role.objects.get(name="Docente")
        pool = [self.docentes_demo["docente"]]
        for n in range(1, 7):
            usuario, _ = User.objects.get_or_create(
                username=f"docente.{n:02d}",
                defaults={"role": rol, "must_change_password": False},
            )
            if not usuario.has_usable_password():
                usuario.set_password(_CONTRASENA)
                usuario.save()
            pool.append(usuario)

        secciones = Section.objects.filter(cycle=self.ciclo, type=Section.TIPO_ACADEMICA)
        cursos = Course.objects.filter(type=Course.TIPO_ACADEMICO).order_by("name")
        creadas = 0
        for s_idx, seccion in enumerate(secciones.order_by("id")):
            for c_idx, curso in enumerate(cursos):
                if TeacherAssignment.objects.filter(
                    course=curso, section=seccion, cycle=self.ciclo
                ).exists():
                    continue  # ya asignado (p. ej. por seed_demo): se respeta su docente.
                docente = pool[(s_idx + c_idx) % len(pool)]
                crear_asignacion(teacher=docente, course=curso, section=seccion, cycle=self.ciclo)
                creadas += 1
        self.stdout.write(f"Asignaciones docentes nuevas: {creadas}.")

    # -- estudiantes, encargados --------------------------------------------------

    def _sembrar_estudiantes(self):
        rol_familia = Role.objects.get(name="Padre de familia")
        secciones = Section.objects.filter(cycle=self.ciclo, type=Section.TIPO_ACADEMICA)
        nuevos = []
        for seccion in secciones.order_by("id"):
            existentes = Enrollment.objects.filter(
                section=seccion, cycle=self.ciclo, is_active=True
            ).count()
            for _ in range(max(0, _POR_SECCION - existentes)):
                edad = _EDAD_POR_GRADO.get(seccion.grade, 14)
                nacimiento = date(2026 - edad, self.rng.randint(1, 12), self.rng.randint(1, 28))
                estudiante = crear_estudiante(
                    first_name=self.rng.choice(_NOMBRES),
                    last_name=f"{self.rng.choice(_APELLIDOS)} {self.rng.choice(_APELLIDOS)}",
                    birth_date=nacimiento,
                    address="Zona 1, San Juan Sacatepéquez",
                )
                inscribir_estudiante(
                    student=estudiante,
                    section=seccion,
                    cycle=self.ciclo,
                    enrolled_at=self.ciclo.start_date,
                )
                nuevos.append(estudiante)

        # Un encargado por cada dos estudiantes nuevos (hermanos), así el
        # portal público se prueba con familias de uno y de dos hijos.
        # `familia.demo` no cuenta: la numeración arranca en familia.01.
        siguiente = (
            User.objects.filter(username__regex=r"^familia\.\d+$")
            .exclude(username="familia.demo")
            .count()
        )
        for i in range(0, len(nuevos), 2):
            siguiente += 1
            usuario = User.objects.create_user(
                username=f"familia.{siguiente:02d}",
                password=_CONTRASENA,
                role=rol_familia,
                must_change_password=False,
            )
            encargado = crear_encargado(
                user=usuario,
                full_name=f"Encargado {siguiente:02d} {nuevos[i].last_name.split()[0]}",
                phone=f"5{self.rng.randint(1000000, 9999999)}",
            )
            for j, hijo in enumerate(nuevos[i : i + 2]):
                vincular_encargado_estudiante(
                    guardian=encargado,
                    student=hijo,
                    relationship=self.rng.choice(["Madre", "Padre", "Tía"]),
                    is_primary=(j == 0),
                )
        self.stdout.write(f"Estudiantes nuevos: {len(nuevos)}.")

    # -- pagos --------------------------------------------------------------------

    def _sembrar_pagos(self):
        hoy = timezone.localdate()
        meses = sorted(
            meses_del_periodo(inicio=self.ciclo.start_date, hasta=min(hoy, self.ciclo.end_date))
        )
        beca = Scholarship.objects.filter(name="Beca completa").first()
        pagos = 0
        inscripciones = Enrollment.objects.filter(
            cycle=self.ciclo, section__type=Section.TIPO_ACADEMICA, is_active=True
        ).select_related("student")
        for inscripcion in inscripciones:
            if Payment.objects.filter(enrollment=inscripcion).exists():
                continue
            if inscripcion.student.internal_code in self._codigos_de_demo():
                continue  # los 4 de seed_demo ya traen su mezcla de solvencia.
            perfil = _elegir(random.Random(inscripcion.student.internal_code), _PERFILES_PAGO)
            if perfil == "becado" and beca and inscripcion.scholarship_id is None:
                inscripcion.scholarship = beca
                inscripcion.save(update_fields=["scholarship"])
            a_pagar = {"al_dia": meses, "atrasado": meses[:2]}.get(perfil, [])
            for anio, mes in a_pagar:
                registrar_pago(
                    enrollment=inscripcion,
                    period_month=mes,
                    period_year=anio,
                    amount=Decimal("150.00"),
                    payment_date=date(anio, mes, 1),
                    receipt_number=f"MAS-{inscripcion.student.internal_code}-{anio}{mes:02d}",
                    recorded_by=self.docentes_demo["pagos"],
                )
                pagos += 1
        self.stdout.write(f"Pagos nuevos: {pagos}.")

    def _codigos_de_demo(self):
        if not hasattr(self, "_demo"):
            self._demo = set(
                Student.objects.order_by("internal_code").values_list("internal_code", flat=True)[
                    :4
                ]
            )
        return self._demo

    # -- actividades y notas ------------------------------------------------------

    def _sembrar_actividades_y_notas(self):
        tipos = {t.name: t for t in ActivityType.objects.all()}
        # Perfil fijo por inscripción: un estudiante flojo lo es en todos los cursos.
        perfiles = {}
        asignaciones = TeacherAssignment.objects.filter(
            cycle=self.ciclo, course__type=Course.TIPO_ACADEMICO, is_active=True
        ).select_related("course", "section", "teacher")
        total_notas = 0
        for asignacion in asignaciones:
            inscripciones = list(
                Enrollment.objects.filter(
                    section=asignacion.section,
                    cycle=self.ciclo,
                    is_active=True,
                    status=Enrollment.ESTADO_ACTIVO,
                )
            )
            for numero in _UNIDADES_CON_NOTAS:
                unidad = self.unidades[numero]
                if Activity.objects.filter(assignment=asignacion, unit=unidad).exists():
                    continue
                duracion = (unidad.end_date - unidad.start_date).days
                for i, (tipo, nombre, maximo) in enumerate(_DISENO_UNIDAD):
                    actividad = crear_actividad(
                        assignment=asignacion,
                        unit=unidad,
                        activity_type=tipos[tipo],
                        name=nombre,
                        max_score=Decimal(maximo),
                        due_date=unidad.start_date
                        + timedelta(days=int(duracion * (i + 1) / (len(_DISENO_UNIDAD) + 1))),
                    )
                    for inscripcion in inscripciones:
                        perfil = perfiles.setdefault(inscripcion.id, _elegir(self.rng, _PERFILES))
                        _, media, ruido = _PERFILES[perfil]
                        fraccion = min(1.0, max(0.0, self.rng.gauss(media, ruido)))
                        punteo = (Decimal(maximo) * Decimal(str(fraccion))).quantize(Decimal("0.5"))
                        registrar_punteo(
                            enrollment=inscripcion,
                            activity=actividad,
                            raw_score=min(punteo, Decimal(maximo)),
                            recorded_by=asignacion.teacher,
                        )
                        total_notas += 1
        self.stdout.write(f"Notas nuevas: {total_notas} (unidades 1 a 3).")

    # -- asistencia y justificaciones ---------------------------------------------

    def _sembrar_asistencia(self):
        if Attendance.objects.count() > 20:
            return
        hoy = timezone.localdate()
        dias = []
        cursor = hoy
        while len(dias) < 20:
            if cursor.weekday() < 5 and self.ciclo.start_date <= cursor <= self.ciclo.end_date:
                dias.append(cursor)
            cursor -= timedelta(days=1)
        estados = [
            (Attendance.ESTADO_PRESENTE, 0.85),
            (Attendance.ESTADO_TARDE, 0.06),
            (Attendance.ESTADO_AUSENTE, 0.09),
        ]
        registros = []
        for inscripcion in Enrollment.objects.filter(
            cycle=self.ciclo, section__type=Section.TIPO_ACADEMICA, is_active=True
        ):
            for dia in dias:
                estado = self.rng.choices([e for e, _ in estados], [p for _, p in estados])[0]
                registros.append(
                    Attendance(
                        enrollment=inscripcion,
                        date=dia,
                        status=estado,
                        recorded_by=self.docentes_demo["docente"],
                    )
                )
        Attendance.objects.bulk_create(registros, ignore_conflicts=True)

        # Justificaciones: de las ausencias, unas pendientes, unas aprobadas y unas rechazadas.
        tipo = JustificationType.objects.filter(requires_document=False).first()
        ausencias = list(Attendance.objects.filter(status=Attendance.ESTADO_AUSENTE)[:24])
        for i, asistencia in enumerate(ausencias):
            justificacion = crear_justificacion(
                attendance=asistencia,
                justification_type=tipo,
                submitted_by=self.docentes_demo["docente"],
                reason_detail="Motivo familiar de prueba (siembra masiva).",
            )
            if i % 3 == 1:
                resolver_justificacion(
                    justificacion, aprobar=True, resolved_by=self.docentes_demo["dir"]
                )
            elif i % 3 == 2:
                resolver_justificacion(
                    justificacion, aprobar=False, resolved_by=self.docentes_demo["dir"]
                )
        self.stdout.write(
            f"Asistencia: {len(registros)} registros, {len(ausencias)} justificaciones."
        )

    # -- cambios de nota ----------------------------------------------------------

    def _sembrar_cambios_de_nota(self):
        from apps.grading.models import GradeChangeRequest

        if GradeChangeRequest.objects.exists():
            return
        calificaciones = list(
            Grade.objects.filter(
                raw_score__lt=Decimal("6"), activity__max_score__gte=10
            ).select_related("activity__assignment__teacher")[:6]
        )
        for i, nota in enumerate(calificaciones):
            solicitud = solicitar_modificacion(
                grade=nota,
                requested_score=min(nota.activity.max_score, nota.raw_score + Decimal("3")),
                reason="Revisión de la prueba: error de suma (siembra masiva).",
                requested_by=nota.activity.assignment.teacher,
            )
            if i % 3 == 1:
                resolver_modificacion(
                    solicitud, aprobar=True, authorized_by=self.docentes_demo["dir"]
                )
            elif i % 3 == 2:
                resolver_modificacion(
                    solicitud, aprobar=False, authorized_by=self.docentes_demo["dir"]
                )
        self.stdout.write(f"Solicitudes de cambio de nota: {len(calificaciones)}.")

    # -- boletines ----------------------------------------------------------------

    def _sembrar_boletines(self):
        """Unidad 1: aprobados y publicados (los insolventes se quedan en
        'aprobado': RN-09 bloquea publicarlos). Unidad 2: aprobados sin
        publicar. Unidad 3: solo borradores. Unidad 4: nada, para generarla
        a mano desde la interfaz."""
        direccion = self.docentes_demo["dir"]
        secciones = Section.objects.filter(cycle=self.ciclo, type=Section.TIPO_ACADEMICA)
        publicados = bloqueados = 0
        for seccion in secciones:
            for numero in (1, 2, 3):
                unidad = self.unidades[numero]
                boletines = generar_boletines(section=seccion, unit=unidad, generated_by=direccion)
                if numero == 3:
                    continue
                for boletin in boletines:
                    if boletin.status == ReportCard.ESTADO_BORRADOR:
                        aprobar_boletin(boletin, approved_by=direccion)
                    if numero == 1 and boletin.status == ReportCard.ESTADO_APROBADO:
                        try:
                            publicar_boletin(boletin)
                            publicados += 1
                        except TransicionDeBoletinInvalida:
                            bloqueados += 1
        self.stdout.write(
            f"Boletines: {ReportCard.objects.count()} en total; unidad 1 publicados {publicados}, "
            f"bloqueados por solvencia/plazo {bloqueados}."
        )
