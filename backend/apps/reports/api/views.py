from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.api.mixins import RegistraAccesoMixin
from apps.core.permissions import PermisoPorArea

from ..selectors.attendance import resumen_asistencia
from ..selectors.enrolled_students import estudiantes_inscritos
from ..selectors.family_access import accesos_de_familias
from ..selectors.grade_change_history import historial_modificaciones
from ..selectors.grades_summary import resumen_notas
from ..selectors.insolvent_students import estudiantes_insolventes
from ..selectors.issued_documents import documentos_emitidos
from ..selectors.metrics import metricas_semanales
from ..selectors.schedules import resumen_horarios
from ..services.pdf_table import render_tabla_pdf


class ReporteBaseView(RegistraAccesoMixin, APIView):
    """Los ocho reportes institucionales (RF-15) comparten la misma forma:
    `?cycle=&section=&format=pdf` — cada subclase solo define el título,
    las columnas y de dónde saca las filas. La única excepción de área es
    `InsolventStudentsView` (ver docs/permisos-roles.md, nota 8: ese
    reporte vive dentro de "Pagos y solvencia" para el rol Encargado de
    pagos, no dentro de "Reportes institucionales")."""

    permission_classes = [PermisoPorArea]
    area = "reportes_institucionales"
    titulo = ""
    columnas: list[tuple[str, str]] = []

    def obtener_filas(self, request) -> list[dict]:
        raise NotImplementedError

    def get(self, request):
        filas = self.obtener_filas(request)
        # No se llama "format": DRF reserva ese nombre de parámetro para su
        # propia negociación de contenido (URL_FORMAT_OVERRIDE) y un
        # "?format=pdf" nunca llega a este método — DRF responde antes,
        # porque no hay ningún renderer registrado para "pdf".
        if request.query_params.get("export") == "pdf":
            pdf_bytes = render_tabla_pdf(titulo=self.titulo, columnas=self.columnas, filas=filas)
            nombre_archivo = f"{self.titulo.lower().replace(' ', '_')}.pdf"
            return HttpResponse(
                pdf_bytes,
                content_type="application/pdf",
                headers={"Content-Disposition": f'attachment; filename="{nombre_archivo}"'},
            )
        return Response({"results": filas})


class GradesSummaryView(ReporteBaseView):
    titulo = "Consolidado de notas"
    columnas = [
        ("student_code", "Código"),
        ("student_name", "Estudiante"),
        ("section", "Sección"),
        ("course", "Curso"),
        ("unit_1_score", "Unidad 1"),
        ("unit_2_score", "Unidad 2"),
        ("unit_3_score", "Unidad 3"),
        ("unit_4_score", "Unidad 4"),
        ("final_score", "Nota final"),
    ]

    def obtener_filas(self, request) -> list[dict]:
        return resumen_notas(
            cycle_id=request.query_params.get("cycle"),
            section_id=request.query_params.get("section"),
        )


class AttendanceReportView(ReporteBaseView):
    titulo = "Asistencia"
    columnas = [
        ("student_code", "Código"),
        ("student_name", "Estudiante"),
        ("section", "Sección"),
        ("presente", "Presente"),
        ("ausente", "Ausente"),
        ("justificado", "Justificado"),
    ]

    def obtener_filas(self, request) -> list[dict]:
        return resumen_asistencia(
            cycle_id=request.query_params.get("cycle"),
            section_id=request.query_params.get("section"),
        )


class PermisoReporteInsolventes(PermisoPorArea):
    """El reporte es institucional: lista a TODOS los insolventes. Que
    `pagos_solvencia` sea `ver` no alcanza (la familia lo tiene para ver la
    solvencia de sus propios hijos, RNF-04): hace falta `editar` en pagos o
    `ver` en reportes institucionales."""

    def has_permission(self, request, view) -> bool:
        if not super().has_permission(request, view):
            return False
        rol = request.user.role
        return (
            rol.nivel_en("pagos_solvencia") == "editar"
            or rol.nivel_en("reportes_institucionales") != "sin_acceso"
        )


class InsolventStudentsView(ReporteBaseView):
    """Nota 8 de docs/permisos-roles.md: para Encargado de pagos, este
    reporte es una vista dentro de "Pagos y solvencia" (área
    `pagos_solvencia`), no de "Reportes institucionales" — el rol nunca
    tiene acceso a los otros siete."""

    permission_classes = [PermisoReporteInsolventes]
    area = "pagos_solvencia"
    titulo = "Estudiantes insolventes"
    columnas = [
        ("student_code", "Código"),
        ("student_name", "Estudiante"),
        ("section", "Sección"),
        ("pending_months", "Meses pendientes"),
    ]

    def obtener_filas(self, request) -> list[dict]:
        return estudiantes_insolventes(
            cycle_id=request.query_params.get("cycle"),
            section_id=request.query_params.get("section"),
        )


class SchedulesReportView(ReporteBaseView):
    titulo = "Horarios"
    columnas = [
        ("section", "Sección"),
        ("course", "Curso"),
        ("teacher", "Docente"),
        ("day_of_week", "Día"),
        ("period_number", "Período"),
    ]

    def obtener_filas(self, request) -> list[dict]:
        return resumen_horarios(section_id=request.query_params.get("section"))


class EnrolledStudentsView(ReporteBaseView):
    titulo = "Estudiantes inscritos"
    columnas = [
        ("student_code", "Código"),
        ("student_name", "Estudiante"),
        ("section", "Sección"),
        ("cycle", "Ciclo"),
        ("status", "Estado"),
        ("scholarship", "Beca"),
    ]

    def obtener_filas(self, request) -> list[dict]:
        return estudiantes_inscritos(
            cycle_id=request.query_params.get("cycle"),
            section_id=request.query_params.get("section"),
        )


class GradeChangeHistoryView(ReporteBaseView):
    titulo = "Historial de modificaciones de notas"
    columnas = [
        ("student_code", "Código"),
        ("student_name", "Estudiante"),
        ("course", "Curso"),
        ("unit", "Unidad"),
        ("original_score", "Nota original"),
        ("requested_score", "Nota propuesta"),
        ("reason", "Motivo"),
        ("requested_by", "Solicitado por"),
        ("status", "Estado"),
        ("authorized_by", "Autorizado por"),
        ("decided_at", "Fecha de decisión"),
    ]

    def obtener_filas(self, request) -> list[dict]:
        return historial_modificaciones(
            cycle_id=request.query_params.get("cycle"),
            section_id=request.query_params.get("section"),
            unit_id=request.query_params.get("unit"),
        )


class FamilyAccessReportView(ReporteBaseView):
    titulo = "Accesos de las familias"
    columnas = [
        ("user", "Usuario"),
        ("screen_viewed", "Pantalla"),
        ("accessed_at", "Fecha"),
    ]

    def obtener_filas(self, request) -> list[dict]:
        return accesos_de_familias()


class IssuedDocumentsReportView(ReporteBaseView):
    titulo = "Documentos emitidos"
    columnas = [
        ("student_code", "Código"),
        ("student_name", "Estudiante"),
        ("section", "Sección"),
        ("document_type", "Tipo"),
        ("issued_at", "Fecha de emisión"),
        ("issued_by", "Emitido por"),
    ]

    def obtener_filas(self, request) -> list[dict]:
        return documentos_emitidos(
            cycle_id=request.query_params.get("cycle"),
            section_id=request.query_params.get("section"),
        )


class MetricsView(RegistraAccesoMixin, APIView):
    """Sección 11: métricas del estudio, sin datos personales — nunca en
    PDF (no es un listado, es un par de porcentajes agregados)."""

    permission_classes = [PermisoPorArea]
    area = "reportes_institucionales"

    def get(self, request):
        return Response(metricas_semanales())
