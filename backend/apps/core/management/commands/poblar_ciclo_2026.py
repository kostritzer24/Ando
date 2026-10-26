# ruff: noqa: E501
"""
Reemplaza los datos de prueba por los datos reales del ciclo 2026 de El
Patojismo CDO, para la capacitación de docentes (oct. 2026).

Lee un JSON preparado a partir de los archivos del centro (horario por
grado y por maestro, consolidados de notas de las 4 unidades y la lista de
docentes y talleristas). Ese JSON trae nombres de estudiantes y notas
reales, así que NO vive en el repositorio: se pasa con --datos.

Qué hace, todo dentro de una sola transacción:

1. Borra los datos de prueba: notas, actividades, boletines, asistencia,
   pagos, documentos, comunicación, horarios, asignaciones, estudiantes,
   encargados, secciones, cursos, bitácora y todos los usuarios (salvo los
   de --conservar). Se quedan los roles, el ciclo con sus unidades y los
   catálogos (tipos de actividad, justificación y documento, becas y
   artículos de convivencia).
2. Crea las cuentas (una por rol: quien es docente y tallerista, o director
   y docente, recibe dos cuentas), con contraseña temporal y cambio
   obligatorio en el primer ingreso.
3. Crea cursos, secciones con su maestro guía, asignaciones y el horario.
4. Inscribe a los estudiantes (fecha de nacimiento aproximada por grado,
   sin encargados).
5. Por cada curso y unidad con notas crea 6 actividades genéricas
   (Actividad 1 a 4 como pruebas cortas de 10 puntos y Actividad 5 y 6 de
   30 puntos) y reparte la nota del consolidado entre ellas, de modo que la
   suma de la unidad da exactamente la nota original.
6. Verifica que cada nota de unidad cuadre con el consolidado.

Sin --ejecutar corre todo y al final deshace la transacción (ensayo
completo, no cambia nada). Con --ejecutar deja los cambios.

    python manage.py poblar_ciclo_2026 --datos ../capacitacion-docentes/datos_ciclo_2026.json
    python manage.py poblar_ciclo_2026 --datos ... --ejecutar
"""

import json
from collections import defaultdict
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.db.models import Sum
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

from apps.accounts.models import Role, User
from apps.attendance.models import Attendance, Justification
from apps.catalog.models import ActivityType, Course, GradingUnit, SchoolCycle, Section
from apps.catalog.services.grading_unit import actualizar_unidad, crear_unidad
from apps.catalog.services.section import crear_seccion
from apps.communication.models import (
    Announcement,
    ConductReport,
    ConductReportArticle,
    Conversation,
    ConversationRead,
    Message,
)
from apps.core.models import AccessLog, AuditLog
from apps.core.services import registrar_cambio
from apps.documents.models import IssuedDocument
from apps.grading.models import Activity, Grade, GradeChangeRequest, ReportCard
from apps.payments.models import Payment
from apps.scheduling.domain.day_structure import HORARIO_POR_JORNADA, jornada_de_grado
from apps.scheduling.models import CalendarEvent, ScheduleBlock, TeacherAssignment
from apps.scheduling.services.schedule_block import CruceDeHorario, crear_bloque
from apps.scheduling.services.teacher_assignment import crear_asignacion
from apps.students.models import Enrollment, Guardian, GuardianStudentLink, Student
from apps.students.services.enrollment import inscribir_estudiante
from apps.students.services.student import crear_estudiante

ANIO = 2026
EDAD_POR_SECCION = {"1A": 13, "1B": 13, "2": 14, "3": 15, "4": 16, "5": 17}
# (nombre, es prueba corta, punteo máximo)
ACTIVIDADES = [
    ("Actividad 1", True, Decimal("10")),
    ("Actividad 2", True, Decimal("10")),
    ("Actividad 3", True, Decimal("10")),
    ("Actividad 4", True, Decimal("10")),
    ("Actividad 5", False, Decimal("30")),
    ("Actividad 6", False, Decimal("30")),
]
CENTAVO = Decimal("0.01")

# Orden de borrado: primero lo que depende de otras tablas. Se usa
# _raw_delete (DELETE directo) porque las llaves foráneas son PROTECT y
# los mensajes cuelgan de la conversación; las restricciones de Postgres son
# diferidas, así que solo se revisan al cerrar la transacción.
BORRAR_EN_ORDEN = [
    ConductReportArticle, ConductReport, ConversationRead, Message, Conversation, Announcement,
    IssuedDocument, Payment,
    ReportCard, GradeChangeRequest, Grade, Activity, Justification, Attendance, CalendarEvent,
    ScheduleBlock, TeacherAssignment, GuardianStudentLink, Enrollment, Guardian, Student,
    Section, Course, AuditLog, AccessLog,
    BlacklistedToken, OutstandingToken,
]  # fmt: skip


class Ensayo(Exception):
    """Se lanza al final de un ensayo para deshacer la transacción."""


def repartir(nota: Decimal) -> list[Decimal]:
    """Reparte la nota de la unidad entre las actividades, proporcional a su
    punteo máximo, y ajusta la última para que la suma sea exacta."""
    partes = [(maximo * nota / 100).quantize(CENTAVO, ROUND_HALF_UP) for *_, maximo in ACTIVIDADES]
    partes[-1] += nota - sum(partes)
    assert all(Decimal(0) <= p <= m for p, (*_, m) in zip(partes, ACTIVIDADES)), (nota, partes)
    return partes


class Command(BaseCommand):
    help = "Borra los datos de prueba y carga los datos reales del ciclo 2026 (capacitación docentes)."

    def add_arguments(self, parser):
        parser.add_argument("--datos", required=True, help="Ruta del JSON con los datos del centro.")
        parser.add_argument(
            "--ejecutar", action="store_true", help="Guarda los cambios (sin esto es un ensayo)."
        )
        parser.add_argument(
            "--conservar", default="", help="Usuarios a no borrar, separados por coma."
        )

    def handle(self, *args, **opts):
        with open(opts["datos"], encoding="utf-8") as f:
            self.datos = json.load(f)
        self.conservar = {u.strip() for u in opts["conservar"].split(",") if u.strip()}
        self.avisos = []
        try:
            with transaction.atomic():
                self._borrar()
                self._cargar()
                self._verificar()
                if not opts["ejecutar"]:
                    # Revisa las llaves foráneas diferidas igual que un COMMIT real.
                    if connection.vendor == "postgresql":
                        with connection.cursor() as cursor:
                            cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
                    raise Ensayo
        except Ensayo:
            self.stdout.write(self.style.WARNING(
                "\nENSAYO: todo corrió bien y se deshizo. Para guardarlo, repetir con --ejecutar."
            ))
        else:
            self.stdout.write(self.style.SUCCESS("\nListo: datos del ciclo 2026 guardados."))
        for aviso in self.avisos:
            self.stdout.write(self.style.WARNING(f"Aviso: {aviso}"))

    # ------------------------------------------------------------------ borrar
    def _borrar(self):
        self.stdout.write("== Borrando datos de prueba")
        for modelo in BORRAR_EN_ORDEN:
            qs = modelo.objects.all()
            total = qs.count()
            qs._raw_delete(qs.db)
            self.stdout.write(f"  {modelo._meta.label:32} {total:>7} borrados")
        usuarios = User.objects.exclude(username__in=self.conservar)
        nombres = list(usuarios.values_list("username", flat=True))
        usuarios._raw_delete(usuarios.db)
        self.stdout.write(f"  usuarios borrados ({len(nombres)}): {', '.join(nombres)}")
        if self.conservar:
            self.stdout.write(f"  usuarios conservados: {', '.join(sorted(self.conservar))}")

    # ------------------------------------------------------------------ cargar
    def _cargar(self):
        d = self.datos
        roles = {r.name: r for r in Role.objects.all()}
        faltan = {c["rol"] for c in d["cuentas"]} - set(roles)
        if faltan:
            raise CommandError(f"Faltan roles en la base: {faltan}. Correr seed_fase3 primero.")

        self.stdout.write("== Cuentas")
        cuentas = sorted(d["cuentas"], key=lambda c: c["rol"] != "Dirección")
        self.usuarios = {}
        director = None
        for c in cuentas:
            if User.objects.filter(username=c["usuario"]).exists():
                raise CommandError(f"El usuario {c['usuario']} ya existe (¿está en --conservar?).")
            u = User.objects.create_user(
                username=c["usuario"], password=c["clave"], role=roles[c["rol"]],
                must_change_password=True, email=c["correo"],
                first_name=c["nombres"], last_name=c["apellidos"],
            )  # fmt: skip
            director = director or u
            registrar_cambio(
                usuario=director, entidad_nombre="accounts.User", entidad_id=u.id,
                accion="crear", valor_nuevo={"username": u.username, "role": c["rol"]},
            )  # fmt: skip
            self.usuarios[c["usuario"]] = u
            self.stdout.write(f"  {c['rol']:11} {u.username}")
        self.director = director

        self.stdout.write("== Ciclo y unidades (un bimestre por unidad)")
        inicio_ciclo = date.fromisoformat(d["ciclo"]["inicio"])
        fin_ciclo = date.fromisoformat(d["ciclo"]["fin"])
        ciclo = SchoolCycle.objects.filter(year=ANIO).first()
        if ciclo is None:
            ciclo = SchoolCycle.objects.create(
                year=ANIO, start_date=inicio_ciclo, end_date=fin_ciclo, status=SchoolCycle.ESTADO_ACTIVO
            )
        # El ciclo se abre primero lo suficiente para que quepan las fechas
        # viejas y las nuevas; al final queda con las fechas reales.
        ciclo.start_date = min(ciclo.start_date, inicio_ciclo)
        ciclo.end_date = max(ciclo.end_date, fin_ciclo)
        ciclo.save(update_fields=["start_date", "end_date", "updated_at"])
        existentes = {u.number: u for u in GradingUnit.objects.filter(cycle=ciclo, is_active=True)}
        # De la 4 a la 1: así una unidad nueva nunca se encima con la fecha
        # vieja de la siguiente.
        for u in sorted(d["unidades"], key=lambda u: -u["numero"]):
            inicio, cierre = date.fromisoformat(u["inicio"]), date.fromisoformat(u["fin"])
            if u["numero"] in existentes:
                actualizar_unidad(existentes[u["numero"]], number=u["numero"], start_date=inicio, end_date=cierre)
            else:
                crear_unidad(cycle=ciclo, number=u["numero"], start_date=inicio, end_date=cierre)
            self.stdout.write(f"  Unidad {u['numero']}: {inicio:%d/%m} al {cierre:%d/%m}")
        ciclo.start_date, ciclo.end_date = inicio_ciclo, fin_ciclo
        ciclo.save(update_fields=["start_date", "end_date", "updated_at"])
        self.ciclo = ciclo
        self.unidades = {u.number: u for u in GradingUnit.objects.filter(cycle=ciclo)}

        self.stdout.write("== Cursos y secciones")
        cursos = {}
        for nombre in sorted({a["curso"] for a in d["asignaciones"]}):
            cursos[nombre] = Course.objects.create(name=nombre, type=Course.TIPO_ACADEMICO)
        for t in d["talleres"]:
            cursos[t["taller"]] = Course.objects.create(name=t["taller"], type=Course.TIPO_TALLER)
        secciones = {}
        for s in d["secciones"]:
            secciones[s["clave"]] = crear_seccion(
                cycle=ciclo, grade=s["grado"], letter=s["letra"], type=Section.TIPO_ACADEMICA,
                homeroom_teacher=self.usuarios[s["guia"]] if s["guia"] else None,
            )  # fmt: skip
        self.stdout.write(f"  {len(cursos)} cursos, {len(secciones)} secciones académicas")

        self.stdout.write("== Asignaciones y horario")
        self.asignaciones = {}
        for a in d["asignaciones"]:
            self.asignaciones[(a["curso"], a["seccion"])] = crear_asignacion(
                teacher=self.usuarios[a["docente"]], course=cursos[a["curso"]],
                section=secciones[a["seccion"]], cycle=ciclo,
            )  # fmt: skip
        bloques_taller = 0
        for t in d["talleres"]:
            seccion = crear_seccion(
                cycle=ciclo, grade=f"Taller de {t['taller'].lower()}", letter="",
                type=Section.TIPO_TALLER,
            )  # fmt: skip
            asignacion_taller = crear_asignacion(
                teacher=self.usuarios[t["tallerista"]], course=cursos[t["taller"]],
                section=seccion, cycle=ciclo,
            )  # fmt: skip
            for dia in t.get("dias", []):
                for periodo in t.get("periodos", []):
                    try:
                        crear_bloque(assignment=asignacion_taller, day_of_week=dia, period_number=periodo)
                        bloques_taller += 1
                    except CruceDeHorario as exc:
                        self.avisos.append(f"Horario de taller no cargado, {t['taller']} {dia} período {periodo}: {exc}")
        bloques = 0
        # Primero los bloques de los horarios de cada maestro; los cursos que
        # se le dieron al maestro guía (sin docente en el horario) van al
        # final, para que un choque nunca le quite una clase real a nadie.
        por_guia = {(a["curso"], a["seccion"]) for a in d["asignaciones"] if a.get("por_guia")}
        for b in sorted(d["bloques"], key=lambda b: (b["curso"], b["seccion"]) in por_guia):
            asignacion = self.asignaciones[(b["curso"], b["seccion"])]
            jornada = jornada_de_grado(asignacion.section.grade)
            periodo = next(
                (n for n, (ini, _) in HORARIO_POR_JORNADA[jornada].items()
                 if n <= 6 and ini.strftime("%-H:%M") == b["hora"]),
                None,
            )  # fmt: skip
            if periodo is None:
                self.avisos.append(f"Hora sin período: {b} ({jornada})")
                continue
            try:
                crear_bloque(assignment=asignacion, day_of_week=b["dia"], period_number=periodo)
                bloques += 1
            except CruceDeHorario as exc:
                self.avisos.append(f"Horario no cargado, {b['curso']} {b['seccion']} {b['dia']} {b['hora']}: {exc}")
        self.stdout.write(
            f"  {len(self.asignaciones)} asignaciones, {bloques} bloques de la mañana; "
            f"{len(d['talleres'])} talleres con {bloques_taller} bloques de la tarde"
        )

        self.stdout.write("== Estudiantes")
        self.inscripciones = []
        for e in d["estudiantes"]:
            est = crear_estudiante(
                first_name=e["nombres"], last_name=e["apellidos"],
                birth_date=date(ANIO - EDAD_POR_SECCION[e["seccion"]], 1, 1),
            )  # fmt: skip
            insc = inscribir_estudiante(
                student=est, section=secciones[e["seccion"]], cycle=ciclo, enrolled_at=ciclo.start_date
            )
            self.inscripciones.append((insc, e))
        self.stdout.write(f"  {len(self.inscripciones)} estudiantes inscritos")

        self._cargar_notas()

    def _cargar_notas(self):
        self.stdout.write("== Actividades y notas")
        tipo_prueba = ActivityType.objects.filter(counts_as_short_quiz=True, is_active=True).first()
        tipo_otra = ActivityType.objects.filter(counts_as_short_quiz=False, is_active=True).first()
        if tipo_prueba is None:
            tipo_prueba = ActivityType.objects.create(name="Prueba corta", counts_as_short_quiz=True)
        if tipo_otra is None:
            tipo_otra = ActivityType.objects.create(name="Tarea", counts_as_short_quiz=False)

        # (curso, sección, unidad) que tienen al menos una nota
        con_notas = {
            (curso, e["seccion"], int(u))
            for _, e in self.inscripciones for u, notas in e["notas"].items() for curso in notas
        }  # fmt: skip
        nuevas = []
        for curso, sec, u in sorted(con_notas):
            unidad = self.unidades[u]
            paso = (unidad.end_date - unidad.start_date) / (len(ACTIVIDADES) + 1)
            for i, (nombre, prueba, maximo) in enumerate(ACTIVIDADES, start=1):
                nuevas.append(Activity(
                    assignment=self.asignaciones[(curso, sec)], unit=unidad,
                    activity_type=tipo_prueba if prueba else tipo_otra, name=nombre,
                    max_score=maximo, due_date=unidad.start_date + timedelta(days=paso.days * i),
                ))  # fmt: skip
        actividades = Activity.objects.bulk_create(nuevas, batch_size=500)
        indice = defaultdict(list)
        for act in actividades:
            indice[(act.assignment_id, act.unit_id)].append(act)
        self._bitacora(
            [(a.assignment.teacher, a.id, {"name": a.name, "activity_type": a.activity_type.name,
              "max_score": str(a.max_score), "due_date": a.due_date.isoformat()}) for a in actividades],
            "grading.Activity",
        )  # fmt: skip

        notas = []
        for insc, e in self.inscripciones:
            for u, por_curso in e["notas"].items():
                unidad = self.unidades[int(u)]
                for curso, valor in por_curso.items():
                    asig = self.asignaciones[(curso, e["seccion"])]
                    acts = sorted(indice[(asig.id, unidad.id)], key=lambda a: a.name)
                    for act, punteo in zip(acts, repartir(Decimal(str(valor)).quantize(CENTAVO))):
                        notas.append(Grade(
                            enrollment=insc, activity=act, raw_score=punteo, current_score=punteo,
                            source=Grade.ORIGEN_PLANTILLA, recorded_by=asig.teacher,
                        ))  # fmt: skip
        creadas = Grade.objects.bulk_create(notas, batch_size=1000)
        self._bitacora(
            [(g.recorded_by, g.id, {"enrollment": str(g.enrollment.public_id), "activity": str(g.activity.public_id),
              "raw_score": str(g.raw_score), "source": g.source}) for g in creadas],
            "grading.Grade",
        )  # fmt: skip
        self.stdout.write(f"  {len(actividades)} actividades, {len(creadas)} notas")

    def _bitacora(self, filas, entidad):
        AuditLog.objects.bulk_create(
            [AuditLog(user=u, entity_name=entidad, entity_id=i, action="crear", new_value=v) for u, i, v in filas],
            batch_size=1000,
        )

    # --------------------------------------------------------------- verificar
    def _verificar(self):
        self.stdout.write("== Verificación contra los consolidados")
        sumas = {
            (r["enrollment"], r["activity__assignment"], r["activity__unit"]): r["total"]
            for r in Grade.objects.values("enrollment", "activity__assignment", "activity__unit")
            .annotate(total=Sum("current_score"))
        }  # fmt: skip
        revisadas = malas = 0
        for insc, e in self.inscripciones:
            for u, por_curso in e["notas"].items():
                for curso, valor in por_curso.items():
                    clave = (insc.id, self.asignaciones[(curso, e["seccion"])].id, self.unidades[int(u)].id)
                    revisadas += 1
                    if sumas.get(clave) != Decimal(str(valor)).quantize(CENTAVO):
                        malas += 1
                        self.avisos.append(f"No cuadra {e['apellidos']} {curso} U{u}: {sumas.get(clave)} vs {valor}")
        if malas:
            raise CommandError(f"{malas} notas de unidad no cuadran con el consolidado; no se guardó nada.")
        self.stdout.write(f"  {revisadas} notas de unidad revisadas, todas cuadran.")
        self.stdout.write(
            f"  Totales: {User.objects.count()} usuarios, {Student.objects.count()} estudiantes, "
            f"{TeacherAssignment.objects.count()} asignaciones, {ScheduleBlock.objects.count()} bloques, "
            f"{Activity.objects.count()} actividades, {Grade.objects.count()} notas"
        )
