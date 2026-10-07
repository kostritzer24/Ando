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


NUMERO_DE_UNIDADES = 4


def nivel_del_grado(grado: str) -> str:
    """Subtítulo del cuadro de notas institucional ("Ciclo Diversificado" en
    el formato de Quinto Bachillerato). Si el grado no es reconocible no se
    inventa un nivel: el membrete simplemente lo omite."""
    minuscula = grado.lower()
    if "bachillerato" in minuscula or "diversificado" in minuscula:
        return "Ciclo Diversificado"
    if "básico" in minuscula or "basico" in minuscula:
        return "Ciclo Básico"
    return ""


def armar_fila_cuadro(notas_por_unidad: dict[int, Decimal]) -> dict:
    """Una fila del cuadro de notas (formato institucional: Unidad 1 a 4,
    Promedio Final y A/R). Una unidad sin nota queda en blanco y no entra
    al promedio — como el `AVERAGE` de la hoja de cálculo del centro. El
    promedio y la aprobación salen de `scoring.py` (RN-02/RN-03)."""
    unidades = [notas_por_unidad.get(numero) for numero in range(1, NUMERO_DE_UNIDADES + 1)]
    con_nota = [nota for nota in unidades if nota is not None]
    promedio = calcular_nota_final(con_nota) if con_nota else None
    return {
        "unidades": unidades,
        "promedio": promedio,
        "aprobado": None if promedio is None else aprueba_curso(promedio),
    }


def promedio_de_unidades(filas: list[dict]) -> list[int | None]:
    """Fila "Promedio de Unidad" del cuadro: el promedio de todos los cursos
    en cada columna, más el general en la última posición."""
    columnas = []
    for indice in range(NUMERO_DE_UNIDADES):
        notas = [fila["unidades"][indice] for fila in filas if fila["unidades"][indice] is not None]
        columnas.append(calcular_nota_final(notas) if notas else None)
    promedios = [fila["promedio"] for fila in filas if fila["promedio"] is not None]
    columnas.append(calcular_nota_final([Decimal(p) for p in promedios]) if promedios else None)
    return columnas


def formatear_nota(nota) -> str:
    """85.00 → "85", 85.50 → "85.5": sin ceros de relleno en los textos
    que se le muestran a Dirección (pendientes del boletín)."""
    texto = f"{Decimal(nota):f}"
    return texto.rstrip("0").rstrip(".") if "." in texto else texto
