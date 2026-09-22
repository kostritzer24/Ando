"""
Comando de siembra de demostración: parte de `seed_fase3` (roles y
usuarios de prueba) y agrega datos maestros reales — un ciclo escolar con
sus 4 unidades, las 6 secciones de la jornada matutina más una de taller
(sección 1 del prompt maestro), cursos, catálogos y los artículos del
código de convivencia de `docs/reporte.docx` (ADR-0006).

Es el mismo comando que se sigue extendiendo fase a fase hasta llegar al
"sistema listo para demostración" de la sección 16 del prompt maestro —
no se crea un comando nuevo por cada fase.
"""

from datetime import date

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

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


class Command(BaseCommand):
    help = "Siembra de demostración: roles, usuarios y datos maestros (fases 3 y 4)."

    @transaction.atomic
    def handle(self, *args, **options):
        call_command("seed_fase3")

        ciclo, creado = SchoolCycle.objects.get_or_create(
            year=2026,
            defaults={
                "start_date": "2026-01-12",
                "end_date": "2026-10-30",
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

        self.stdout.write(self.style.SUCCESS("Siembra de demostración lista (fases 3 y 4)."))
