"""RF-09 / RN-09 / RN-10: el flujo de un boletín es borrador → aprobado →
publicado, y publicar exige además que se hayan cumplido los plazos de
RN-10 y que la inscripción esté solvente (RN-09). Las cadenas de estado
las pasa quien llama (`grading/services/report_card.py`), no se importa
el modelo acá para mantener el dominio sin depender de Django."""


class TransicionDeBoletinInvalida(Exception):
    pass


def validar_aprobacion(*, estado_actual: str, estado_borrador: str) -> None:
    if estado_actual != estado_borrador:
        raise TransicionDeBoletinInvalida("Solo se puede aprobar un boletín que está en borrador.")


def validar_publicacion(
    *, estado_actual: str, estado_aprobado: str, plazo_cumplido: bool, es_solvente: bool
) -> None:
    if estado_actual != estado_aprobado:
        raise TransicionDeBoletinInvalida("Solo se puede publicar un boletín que ya fue aprobado.")
    if not plazo_cumplido:
        raise TransicionDeBoletinInvalida(
            "Todavía no se cumple el plazo para habilitar el boletín (RN-10)."
        )
    if not es_solvente:
        raise TransicionDeBoletinInvalida(
            "El estudiante no está solvente; no se puede publicar el boletín (RN-09)."
        )
