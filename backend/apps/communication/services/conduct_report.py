from apps.catalog.models import ConductRuleArticle

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


# Rótulos tal como aparecen en el formato institucional (reporte.docx.pdf).
_GRAVEDADES = [
    (ConductReport.LEVE, "FALTA LEVE", "Llamado de atención, amonestación escrita"),
    (ConductReport.GRAVE, "FALTA GRAVE", "Reporte oficial, comunicación a familia"),
    (ConductReport.MUY_GRAVE, "FALTA MUY GRAVE", "Suspensión, expulsión"),
]

# (sanction_type, texto, espacio en blanco que el formato deja para llenar)
_SANCIONES = [
    (ConductReport.LLAMADO_VERBAL, "Llamado de atención verbal", ""),
    (ConductReport.AMONESTACION_ESCRITA, "Amonestación escrita (este documento)", ""),
    (ConductReport.COMUNICACION_FAMILIA, "Comunicación oficial a la familia", ""),
    (
        ConductReport.SUSPENSION_EXTRACURRICULAR,
        "Suspensión de actividades extracurriculares",
        "por __ días",
    ),
    (ConductReport.SERVICIO_COMUNITARIO, "Servicio comunitario escolar:", "______"),
    (ConductReport.SUSPENSION_CLASES, "Suspensión de clases", "por _ días (del __ al __)"),
    (ConductReport.EVALUACION_EXPULSION, "Evaluación de expulsión", ""),
    (ConductReport.OTRA_SANCION, "Otra:", "____________"),
]


def _numero_de_articulo(codigo: str) -> int:
    digitos = "".join(caracter for caracter in codigo if caracter.isdigit())
    return int(digitos) if digitos else 0


def _capitulos_del_codigo(marcados: set[int]) -> list[dict]:
    """El catálogo completo, agrupado por capítulo en el orden del
    formato impreso (Art. 9, 10, 11 — no el orden alfabético de `code`),
    con los artículos de este reporte marcados."""
    articulos = sorted(
        ConductRuleArticle.objects.filter(is_active=True),
        key=lambda a: (a.chapter, _numero_de_articulo(a.code), a.id),
    )
    capitulos: list[dict] = []
    for articulo in articulos:
        if not capitulos or capitulos[-1]["nombre"] != articulo.chapter:
            capitulos.append({"nombre": articulo.chapter, "articulos": []})
        capitulos[-1]["articulos"].append(
            {
                "codigo": articulo.code,
                "descripcion": articulo.description,
                "marcado": articulo.id in marcados,
            }
        )
    return capitulos


def _repartir_en_dos_columnas(capitulos: list[dict]) -> list[list[dict]]:
    """Reparte los capítulos en dos columnas de alto parecido, sin partir
    un capítulo a la mitad (el formato impreso tampoco los parte)."""
    total = sum(len(c["articulos"]) + 1 for c in capitulos)
    izquierda: list[dict] = []
    acumulado = 0
    for indice, capitulo in enumerate(capitulos):
        if acumulado >= total / 2 and indice > 0:
            break
        izquierda.append(capitulo)
        acumulado += len(capitulo["articulos"]) + 1
    return [izquierda, capitulos[len(izquierda) :]]


def contenido_reporte(reporte: ConductReport) -> dict:
    """RF-24. Contexto del PDF "Reporte de incidencia": el formato
    institucional lista TODAS las opciones y deja marcadas las que aplican,
    así que acá se arma el catálogo completo, no solo lo registrado."""
    marcados = set(
        ConductReportArticle.objects.filter(conduct_report=reporte).values_list(
            "article_id", flat=True
        )
    )
    inscripcion = reporte.enrollment
    sanciones = [
        {
            "texto": texto,
            "blanco": blanco,
            "marcada": tipo == reporte.sanction_type,
            "detalle": reporte.sanction_detail if tipo == reporte.sanction_type else "",
        }
        for tipo, texto, blanco in _SANCIONES
    ]
    compromisos = [linea.strip() for linea in reporte.commitments.splitlines() if linea.strip()]
    compromisos += ["_____________________"] * max(0, 3 - len(compromisos))
    return {
        "reporte": reporte,
        "estudiante_nombre": inscripcion.student.nombre_completo(),
        "grado_seccion": str(inscripcion.section),
        "fecha": reporte.report_date.strftime("%d/%m/%Y"),
        "gravedades": [
            {"nombre": nombre, "detalle": detalle, "marcada": clave == reporte.severity}
            for clave, nombre, detalle in _GRAVEDADES
        ],
        "columnas_normas": _repartir_en_dos_columnas(_capitulos_del_codigo(marcados)),
        "columnas_sanciones": [sanciones[:4], sanciones[4:]],
        "compromisos": compromisos,
    }
