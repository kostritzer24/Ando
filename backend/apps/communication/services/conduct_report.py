from ..models import ConductReport, ConductReportArticle


def crear_reporte(*, guide_teacher, article_ids: list[int] | None = None, **datos) -> ConductReport:
    """RF-24. Los artículos incumplidos son un checklist opcional sobre el
    catálogo (ADR-0006) — `other_violation_detail` cubre lo que no calza
    en ningún artículo."""
    reporte = ConductReport.objects.create(guide_teacher=guide_teacher, **datos)
    if article_ids:
        ConductReportArticle.objects.bulk_create(
            [
                ConductReportArticle(conduct_report=reporte, article_id=article_id)
                for article_id in article_ids
            ]
        )
    return reporte
