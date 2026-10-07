"""RF-09 / RN-09 / RN-10: el flujo de un boletín es borrador → aprobado →
publicado, y publicar exige además que se hayan cumplido los plazos de
RN-10 y que la inscripción esté solvente (RN-09). Las cadenas de estado
las pasa quien llama (`grading/services/report_card.py`), no se importa
el modelo acá para mantener el dominio sin depender de Django."""

from decimal import Decimal

from .scoring import aprueba_curso, calcular_nota_final


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


TOTAL_UNIDADES = 4


def formatear_nota(nota) -> str:
    """85.00 → "85", 85.50 → "85.5": el boletín no muestra ceros de relleno."""
    texto = f"{Decimal(nota):f}"
    return texto.rstrip("0").rstrip(".") if "." in texto else texto


def armar_filas_del_boletin(
    *, cursos: list[tuple[str, list[Decimal]]], unidad_actual: int
) -> list[dict]:
    """Una fila por curso con la nota de cada unidad hasta la actual. La
    nota final y si aprueba (RN-02/RN-03) solo aparecen en el boletín de la
    última unidad: RN-03 define la aprobación del curso por la nota final,
    así que marcar "Reprobado" una unidad suelta decía algo que la regla no
    dice."""
    filas = []
    for nombre, notas in cursos:
        fila = {"nombre": nombre, "notas": [formatear_nota(n) for n in notas]}
        if unidad_actual == TOTAL_UNIDADES and len(notas) == TOTAL_UNIDADES:
            final = calcular_nota_final(notas)
            fila["final"] = final
            fila["aprobado"] = aprueba_curso(final)
        filas.append(fila)
    return filas
