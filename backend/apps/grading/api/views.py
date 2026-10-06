from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView
from weasyprint import HTML

from apps.catalog.models import GradingUnit
from apps.core.api.mixins import RegistraAccesoMixin, ScopedQuerysetMixin
from apps.core.permissions import PermisoPorArea
from apps.scheduling.models import TeacherAssignment

from ..domain.grade_change import SolicitudDeModificacionInvalida
from ..domain.report_card import TransicionDeBoletinInvalida
from ..domain.unit_design import DefinicionDeUnidadInvalida
from ..models import Activity, Grade, GradeChangeRequest, ReportCard
from ..services.activity import (
    AsignacionNoCalifica,
    actualizar_actividad,
    crear_actividad,
    dar_de_baja_actividad,
)
from ..services.grade import InscripcionAjena, PunteoFueraDeRango, YaCalificado, registrar_punteo
from ..services.grade_change_request import resolver_modificacion, solicitar_modificacion
from ..services.report_card import (
    aprobar_boletin,
    contenido_boletin,
    generar_boletines,
    publicar_boletin,
)
from ..services.template import (
    ArchivoIlegible,
    UnidadSinActividades,
    aplicar_plantilla,
    generar_plantilla,
    validar_y_clasificar_plantilla,
)
from .serializers import (
    ActivitySerializer,
    ActivityUpdateSerializer,
    GradeChangeRequestSerializer,
    GradeCreateSerializer,
    GradeSerializer,
    ReportCardGenerateSerializer,
    ReportCardSerializer,
)

_ROLES_SIN_ALCANCE_LIMITADO = {
    "Dirección",
    "Coordinación",
    "Encargado de pagos",
    "Administrador del sistema",
}
_ROLES_SIN_ALCANCE_LIMITADO_BOLETIN = {"Dirección", "Coordinación", "Administrador del sistema"}
_ROLES_DOCENTES_QUE_CALIFICAN = {"Docente", "Docente con sección a cargo"}
ROL_DIRECCION = "Dirección"


class _SoloDireccion(BasePermission):
    """`docs/api.md` documenta generar, aprobar y publicar boletines como
    `DIR (E)` únicamente — más estricto que el `E` que DOC/GUÍA tienen en
    el área "notas" para actividades y calificaciones."""

    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.role.name == ROL_DIRECCION)


def _requiere_asignacion_propia(user, assignment: TeacherAssignment) -> None:
    if user.role.name in _ROLES_DOCENTES_QUE_CALIFICAN and assignment.teacher_id != user.id:
        raise PermissionDenied("Esa asignación docente no es tuya.")


class ActivityViewSet(RegistraAccesoMixin, ScopedQuerysetMixin, viewsets.ModelViewSet):
    """RF-17. Editar y dar de baja pasan por sus servicios: el tope de 100
    puntos se vuelve a validar, una actividad calificada no cambia su
    máximo ni se da de baja, y nada se borra de verdad."""

    queryset = Activity.objects.select_related("assignment", "unit", "activity_type")
    permission_classes = [PermisoPorArea]
    area = "notas"
    lookup_field = "public_id"

    def scope_queryset(self, queryset, user):
        if user.role.name in _ROLES_SIN_ALCANCE_LIMITADO:
            return queryset
        if user.role.name in _ROLES_DOCENTES_QUE_CALIFICAN:
            return queryset.filter(assignment__teacher=user)
        return queryset.none()

    def get_serializer_class(self):
        if self.action in {"update", "partial_update"}:
            return ActivityUpdateSerializer
        return ActivitySerializer

    def perform_create(self, serializer):
        datos = serializer.validated_data
        _requiere_asignacion_propia(self.request.user, datos["assignment"])
        try:
            serializer.instance = crear_actividad(usuario=self.request.user, **datos)
        except (AsignacionNoCalifica, DefinicionDeUnidadInvalida) as exc:
            raise ValidationError(str(exc)) from exc

    @extend_schema(request=ActivityUpdateSerializer, responses=ActivitySerializer)
    def update(self, request, *args, **kwargs):
        actividad = self.get_object()
        _requiere_asignacion_propia(request.user, actividad.assignment)
        serializer = ActivityUpdateSerializer(
            actividad, data=request.data, partial=kwargs.get("partial", False)
        )
        serializer.is_valid(raise_exception=True)
        try:
            actividad = actualizar_actividad(
                actividad, cambios=serializer.validated_data, usuario=request.user
            )
        except DefinicionDeUnidadInvalida as exc:
            raise ValidationError(str(exc)) from exc
        return Response(ActivitySerializer(actividad).data)

    @extend_schema(request=ActivityUpdateSerializer, responses=ActivitySerializer)
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    def perform_destroy(self, instance):
        _requiere_asignacion_propia(self.request.user, instance.assignment)
        try:
            dar_de_baja_actividad(instance, usuario=self.request.user)
        except DefinicionDeUnidadInvalida as exc:
            raise ValidationError(str(exc)) from exc


class GradeViewSet(
    RegistraAccesoMixin,
    ScopedQuerysetMixin,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """RF-18. Sin editar ni borrar (RN-05): una nota registrada solo cambia
    por una solicitud de modificación que autoriza Dirección. Con PATCH o
    DELETE abiertos, borrar y volver a registrar saltaba esa autorización."""

    queryset = Grade.objects.select_related(
        "enrollment", "activity__assignment__course", "activity__unit", "recorded_by"
    )
    permission_classes = [PermisoPorArea]
    area = "notas"
    lookup_field = "public_id"

    def get_serializer_class(self):
        return GradeCreateSerializer if self.action == "create" else GradeSerializer

    def scope_queryset(self, queryset, user):
        if user.role.name in _ROLES_SIN_ALCANCE_LIMITADO:
            return queryset
        if user.role.name in _ROLES_DOCENTES_QUE_CALIFICAN:
            return queryset.filter(activity__assignment__teacher=user)
        if user.role.name == "Padre de familia":
            return queryset.filter(
                enrollment__student__guardian_links__guardian__user=user,
                enrollment__student__guardian_links__is_active=True,
            ).distinct()
        return queryset.none()

    def create(self, request, *args, **kwargs):
        serializer = GradeCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = serializer.validated_data
        _requiere_asignacion_propia(request.user, datos["activity"].assignment)

        try:
            calificacion = registrar_punteo(
                enrollment=datos["enrollment"],
                activity=datos["activity"],
                raw_score=datos["raw_score"],
                recorded_by=request.user,
            )
        except YaCalificado as exc:
            raise ValidationError(
                {"activity": f"{exc} Si hay que corregirla, usá /grade-change-requests/."}
            ) from exc
        except PunteoFueraDeRango as exc:
            raise ValidationError({"raw_score": str(exc)}) from exc
        except InscripcionAjena as exc:
            raise ValidationError({"enrollment": str(exc)}) from exc
        return Response(GradeSerializer(calificacion).data, status=status.HTTP_201_CREATED)


class GradeChangeRequestViewSet(
    RegistraAccesoMixin,
    ScopedQuerysetMixin,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """RF-23 (solicitar) / RF-10 (autorizar o rechazar)."""

    queryset = GradeChangeRequest.objects.select_related("grade", "requested_by", "authorized_by")
    serializer_class = GradeChangeRequestSerializer
    lookup_field = "public_id"

    def get_permissions(self):
        self.area = "modificacion_notas" if self.action in {"approve", "reject"} else "notas"
        return [PermisoPorArea()]

    def scope_queryset(self, queryset, user):
        if user.role.name in _ROLES_SIN_ALCANCE_LIMITADO:
            return queryset
        if user.role.name in _ROLES_DOCENTES_QUE_CALIFICAN:
            return queryset.filter(grade__activity__assignment__teacher=user)
        return queryset.none()

    def perform_create(self, serializer):
        datos = serializer.validated_data
        _requiere_asignacion_propia(self.request.user, datos["grade"].activity.assignment)
        try:
            serializer.instance = solicitar_modificacion(requested_by=self.request.user, **datos)
        except SolicitudDeModificacionInvalida as exc:
            raise ValidationError({"requested_score": str(exc)}) from exc

    def _resolver(self, request, public_id, aprobar):
        try:
            solicitud = resolver_modificacion(
                self.get_object(), aprobar=aprobar, authorized_by=request.user
            )
        except SolicitudDeModificacionInvalida as exc:
            raise ValidationError(str(exc)) from exc
        return Response(GradeChangeRequestSerializer(solicitud).data)

    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request, public_id=None):
        return self._resolver(request, public_id, aprobar=True)

    @action(detail=True, methods=["post"], url_path="reject")
    def reject(self, request, public_id=None):
        return self._resolver(request, public_id, aprobar=False)


class GradeTemplateDownloadView(RegistraAccesoMixin, APIView):
    """GET /grades/template/{assignment_public_id}/{unit_public_id}/ — RF-19."""

    permission_classes = [PermisoPorArea]
    area = "notas"

    @extend_schema(responses={200: OpenApiTypes.BINARY})
    def get(self, request, assignment_public_id, unit_public_id):
        assignment = get_object_or_404(TeacherAssignment, public_id=assignment_public_id)
        _requiere_asignacion_propia(request.user, assignment)
        unit = get_object_or_404(GradingUnit, public_id=unit_public_id)
        try:
            contenido = generar_plantilla(assignment=assignment, unit=unit)
        except UnidadSinActividades as exc:
            raise ValidationError(str(exc)) from exc

        respuesta = HttpResponse(
            contenido,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        nombre = f"notas_{assignment.course.name}_{unit.number}.xlsx".replace(" ", "_")
        respuesta["Content-Disposition"] = f'attachment; filename="{nombre}"'
        return respuesta


# Una plantilla real de una sección pesa decenas de KB; el límite evita
# abrir archivos enormes (o comprimidos para inflarse) en el servidor.
TAMANO_MAXIMO_PLANTILLA = 2 * 1024 * 1024


def _leer_datos_multipart(request):
    assignment_public_id = request.data.get("assignment")
    unit_public_id = request.data.get("unit")
    archivo = request.FILES.get("file")
    if not (assignment_public_id and unit_public_id and archivo):
        raise ValidationError("Hacen falta 'assignment', 'unit' y 'file'.")
    if not archivo.name.lower().endswith(".xlsx"):
        raise ValidationError("El archivo debe ser un .xlsx — no se aceptan macros (.xlsm).")
    if archivo.size > TAMANO_MAXIMO_PLANTILLA:
        raise ValidationError("El archivo pesa demasiado para ser una plantilla (máximo 2 MB).")
    assignment = get_object_or_404(TeacherAssignment, public_id=assignment_public_id)
    unit = get_object_or_404(GradingUnit, public_id=unit_public_id)
    return assignment, unit, archivo


_ESQUEMA_MULTIPART = {
    "multipart/form-data": {
        "type": "object",
        "properties": {
            "assignment": {"type": "string", "format": "uuid"},
            "unit": {"type": "string", "format": "uuid"},
            "file": {"type": "string", "format": "binary"},
        },
        "required": ["assignment", "unit", "file"],
    }
}


class GradeTemplatePreviewView(RegistraAccesoMixin, APIView):
    """POST /grades/template/preview/ — RF-20, HU-19/20: vista previa sin
    guardar nada."""

    permission_classes = [PermisoPorArea]
    area = "notas"
    parser_classes = [MultiPartParser]

    @extend_schema(
        request=_ESQUEMA_MULTIPART,
        responses={
            200: {
                "type": "object",
                "properties": {
                    "filas": {"type": "integer"},
                    "resumen": {
                        "type": "object",
                        "properties": {
                            "crear": {"type": "integer"},
                            "modificacion": {"type": "integer"},
                            "sin_cambio": {"type": "integer"},
                        },
                    },
                },
            },
            400: {"type": "object", "properties": {"errores": {"type": "array"}}},
        },
    )
    def post(self, request):
        assignment, unit, archivo = _leer_datos_multipart(request)
        _requiere_asignacion_propia(request.user, assignment)
        try:
            filas_validas, errores = validar_y_clasificar_plantilla(
                assignment=assignment, unit=unit, archivo=archivo
            )
        except (UnidadSinActividades, ArchivoIlegible) as exc:
            raise ValidationError(str(exc)) from exc

        if errores:
            return Response({"errores": errores}, status=status.HTTP_400_BAD_REQUEST)

        resumen = {"crear": 0, "modificacion": 0, "sin_cambio": 0}
        for _inscripcion, celdas in filas_validas:
            for celda in celdas:
                resumen[celda["accion"]] += 1
        return Response({"filas": len(filas_validas), "resumen": resumen})


class GradeTemplateUploadView(RegistraAccesoMixin, APIView):
    """POST /grades/template/upload/ — RF-20, RN-07."""

    permission_classes = [PermisoPorArea]
    area = "notas"
    parser_classes = [MultiPartParser]

    @extend_schema(
        request=_ESQUEMA_MULTIPART,
        responses={
            201: {
                "type": "object",
                "properties": {
                    "creados": {"type": "integer"},
                    "solicitudes_de_modificacion": {"type": "integer"},
                },
            },
            400: {"type": "object", "properties": {"errores": {"type": "array"}}},
        },
    )
    def post(self, request):
        assignment, unit, archivo = _leer_datos_multipart(request)
        _requiere_asignacion_propia(request.user, assignment)
        try:
            filas_validas, errores = validar_y_clasificar_plantilla(
                assignment=assignment, unit=unit, archivo=archivo
            )
        except (UnidadSinActividades, ArchivoIlegible) as exc:
            raise ValidationError(str(exc)) from exc

        if errores:
            return Response({"errores": errores}, status=status.HTTP_400_BAD_REQUEST)

        resultado = aplicar_plantilla(filas_validas=filas_validas, recorded_by=request.user)
        return Response(resultado, status=status.HTTP_201_CREATED)


class ReportCardViewSet(
    RegistraAccesoMixin,
    ScopedQuerysetMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """RF-09. Generar es una acción de lote sobre una sección/unidad;
    aprobar y publicar actúan sobre un boletín individual."""

    queryset = ReportCard.objects.select_related(
        "enrollment", "unit", "generated_by", "approved_by"
    )
    serializer_class = ReportCardSerializer
    area = "notas"
    lookup_field = "public_id"

    def get_permissions(self):
        if self.action in {"generate", "approve", "publish"}:
            return [PermisoPorArea(), _SoloDireccion()]
        return [PermisoPorArea()]

    def scope_queryset(self, queryset, user):
        if user.role.name in _ROLES_SIN_ALCANCE_LIMITADO_BOLETIN:
            return queryset
        if user.role.name in _ROLES_DOCENTES_QUE_CALIFICAN:
            return queryset.filter(
                Q(enrollment__section__assignments__teacher=user)
                | Q(enrollment__section__homeroom_teacher=user)
            ).distinct()
        if user.role.name == "Padre de familia":
            return queryset.filter(
                enrollment__student__guardian_links__guardian__user=user,
                enrollment__student__guardian_links__is_active=True,
                status=ReportCard.ESTADO_PUBLICADO,
            ).distinct()
        return queryset.none()

    @action(detail=False, methods=["post"], url_path="generate")
    def generate(self, request):
        serializer = ReportCardGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        boletines = generar_boletines(generated_by=request.user, **serializer.validated_data)
        return Response(
            ReportCardSerializer(boletines, many=True).data, status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request, public_id=None):
        try:
            boletin = aprobar_boletin(self.get_object(), approved_by=request.user)
        except TransicionDeBoletinInvalida as exc:
            raise ValidationError(str(exc)) from exc
        return Response(ReportCardSerializer(boletin).data)

    @action(detail=True, methods=["post"], url_path="publish")
    def publish(self, request, public_id=None):
        try:
            boletin = publicar_boletin(self.get_object(), published_by=request.user)
        except TransicionDeBoletinInvalida as exc:
            raise ValidationError(str(exc)) from exc
        return Response(ReportCardSerializer(boletin).data)

    @action(detail=True, methods=["get"], url_path="download")
    def download(self, request, public_id=None):
        """RF-34. El boletín no guarda un PDF aparte (ver docstring del
        modelo): se genera al momento de la descarga, curso por curso."""
        boletin = self.get_object()
        if boletin.status != ReportCard.ESTADO_PUBLICADO:
            raise ValidationError("Este boletín todavía no está publicado.")
        html = render_to_string("grading/boletin.html", contenido_boletin(boletin))
        pdf_bytes = HTML(string=html).write_pdf()
        nombre_archivo = (
            f"boletin_{boletin.enrollment.student.internal_code}_unidad{boletin.unit.number}.pdf"
        )
        return HttpResponse(
            pdf_bytes,
            content_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{nombre_archivo}"'},
        )
