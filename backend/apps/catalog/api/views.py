from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError

from apps.core.api.mixins import BajaLogicaMixin, RegistraAccesoMixin
from apps.core.permissions import PermisoPorArea

from ..domain.section import MaestroGuiaInvalido
from ..models import (
    ActivityType,
    ConductRuleArticle,
    Course,
    DocumentType,
    GradingUnit,
    JustificationType,
    Scholarship,
    SchoolCycle,
    Section,
)
from ..services.grading_unit import actualizar_unidad, crear_unidad
from ..services.section import actualizar_seccion, crear_seccion
from .serializers import (
    ActivityTypeSerializer,
    ConductRuleArticleSerializer,
    CourseSerializer,
    DocumentTypeSerializer,
    GradingUnitSerializer,
    JustificationTypeSerializer,
    ScholarshipSerializer,
    SchoolCycleSerializer,
    SectionSerializer,
)


class CatalogViewSet(RegistraAccesoMixin, BajaLogicaMixin, viewsets.ModelViewSet):
    """Base común a los 8 catálogos: mismo permiso, mismo identificador de
    URL, misma baja lógica en vez de borrado (RF-02, HU-02)."""

    permission_classes = [PermisoPorArea]
    area = "datos_maestros"
    lookup_field = "public_id"


class SchoolCycleViewSet(CatalogViewSet):
    queryset = SchoolCycle.objects.all()
    serializer_class = SchoolCycleSerializer


class GradingUnitViewSet(CatalogViewSet):
    """Anidada bajo `/cycles/{cycle_public_id}/units/` (`docs/api.md`).
    Las fechas derivadas las calcula siempre el servicio — ver RN-10.

    Misma excepción que `JustificationTypeViewSet`: un docente necesita
    poder elegir la unidad al diseñarla (RF-17) o al generar la
    plantilla de calificaciones (RF-19), aunque "datos_maestros" le dé
    sin_acceso — conoce el `cycle_public_id` por su propia asignación
    (`/assignments/`), así que solo hace falta abrirle la lectura de
    esta ruta anidada, no el catálogo de ciclos completo."""

    serializer_class = GradingUnitSerializer

    def get_permissions(self):
        self.area = "notas" if self.action in {"list", "retrieve"} else "datos_maestros"
        return [PermisoPorArea()]

    def get_queryset(self):
        return GradingUnit.objects.filter(cycle__public_id=self.kwargs["cycle_public_id"])

    def perform_create(self, serializer):
        cycle = get_object_or_404(SchoolCycle, public_id=self.kwargs["cycle_public_id"])
        serializer.instance = crear_unidad(
            cycle=cycle,
            number=serializer.validated_data["number"],
            start_date=serializer.validated_data["start_date"],
            end_date=serializer.validated_data["end_date"],
        )

    def perform_update(self, serializer):
        instancia = serializer.instance
        actualizar_unidad(
            instancia,
            number=serializer.validated_data.get("number", instancia.number),
            start_date=serializer.validated_data.get("start_date", instancia.start_date),
            end_date=serializer.validated_data.get("end_date", instancia.end_date),
        )


class SectionViewSet(CatalogViewSet):
    queryset = Section.objects.all()
    serializer_class = SectionSerializer

    def perform_create(self, serializer):
        datos = serializer.validated_data
        try:
            serializer.instance = crear_seccion(
                cycle=datos["cycle"],
                grade=datos["grade"],
                letter=datos.get("letter", ""),
                type=datos["type"],
                homeroom_teacher=datos.get("homeroom_teacher"),
            )
        except MaestroGuiaInvalido as exc:
            raise ValidationError({"homeroom_teacher": str(exc)}) from exc

    def perform_update(self, serializer):
        instancia = serializer.instance
        datos = serializer.validated_data
        try:
            actualizar_seccion(
                instancia,
                grade=datos.get("grade", instancia.grade),
                letter=datos.get("letter", instancia.letter),
                type=datos.get("type", instancia.type),
                homeroom_teacher=datos.get("homeroom_teacher", instancia.homeroom_teacher),
            )
        except MaestroGuiaInvalido as exc:
            raise ValidationError({"homeroom_teacher": str(exc)}) from exc


class CourseViewSet(CatalogViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer


class ActivityTypeViewSet(CatalogViewSet):
    """Misma excepción que `JustificationTypeViewSet` y `GradingUnitViewSet`:
    un docente necesita elegir el tipo de actividad al diseñar la unidad
    (RF-17), aunque "datos_maestros" le dé sin_acceso."""

    queryset = ActivityType.objects.all()
    serializer_class = ActivityTypeSerializer

    def get_permissions(self):
        self.area = "notas" if self.action in {"list", "retrieve"} else "datos_maestros"
        return [PermisoPorArea()]


class JustificationTypeViewSet(CatalogViewSet):
    """Único de los 8 catálogos con esta excepción: cualquier rol que
    registra una justificación de falta (RF-12 — docente, guía,
    tallerista, no solo Dirección) necesita poder elegir su tipo, aunque
    "Datos maestros" les dé `sin_acceso` (docs/permisos-roles.md). Se
    resuelve como ya se hace en `GradeChangeRequestViewSet`: el área
    cambia según la acción — leer pasa por "asistencia" (donde esos
    roles sí tienen alcance), administrar el catálogo (crear, editar,
    dar de baja) sigue siendo exclusivo de "datos_maestros"."""

    queryset = JustificationType.objects.all()
    serializer_class = JustificationTypeSerializer

    def get_permissions(self):
        self.area = "asistencia" if self.action in {"list", "retrieve"} else "datos_maestros"
        return [PermisoPorArea()]


class DocumentTypeViewSet(CatalogViewSet):
    queryset = DocumentType.objects.all()
    serializer_class = DocumentTypeSerializer


class ScholarshipViewSet(CatalogViewSet):
    queryset = Scholarship.objects.all()
    serializer_class = ScholarshipSerializer


class ConductRuleArticleViewSet(CatalogViewSet):
    """Misma excepción que `ActivityTypeViewSet`/`JustificationTypeViewSet`
    (Fase 11): quien registra un reporte de conducta (RF-24 — Dirección o
    el maestro guía de la sección) necesita elegir los artículos
    incumplidos, aunque "datos_maestros" le dé `sin_acceso` al maestro
    guía. Administrar el catálogo sigue siendo exclusivo de Dirección."""

    queryset = ConductRuleArticle.objects.all()
    serializer_class = ConductRuleArticleSerializer

    def get_permissions(self):
        self.area = "reportes_conducta" if self.action in {"list", "retrieve"} else "datos_maestros"
        return [PermisoPorArea()]
