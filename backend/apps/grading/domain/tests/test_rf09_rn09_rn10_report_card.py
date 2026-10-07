import pytest

from apps.grading.domain.report_card import (
    TransicionDeBoletinInvalida,
    validar_aprobacion,
    validar_publicacion,
)

BORRADOR = "borrador"
APROBADO = "aprobado"
PUBLICADO = "publicado"


def test_se_puede_aprobar_un_boletin_en_borrador():
    validar_aprobacion(estado_actual=BORRADOR, estado_borrador=BORRADOR)


def test_no_se_puede_aprobar_un_boletin_ya_aprobado():
    with pytest.raises(TransicionDeBoletinInvalida):
        validar_aprobacion(estado_actual=APROBADO, estado_borrador=BORRADOR)


def test_se_puede_publicar_un_boletin_aprobado_con_plazo_y_solvencia_cumplidos():
    validar_publicacion(
        estado_actual=APROBADO, estado_aprobado=APROBADO, plazo_cumplido=True, es_solvente=True
    )


def test_no_se_puede_publicar_un_boletin_que_no_esta_aprobado():
    with pytest.raises(TransicionDeBoletinInvalida):
        validar_publicacion(
            estado_actual=BORRADOR, estado_aprobado=APROBADO, plazo_cumplido=True, es_solvente=True
        )


def test_rn10_no_se_puede_publicar_antes_del_plazo():
    with pytest.raises(TransicionDeBoletinInvalida):
        validar_publicacion(
            estado_actual=APROBADO, estado_aprobado=APROBADO, plazo_cumplido=False, es_solvente=True
        )


def test_rn09_no_se_puede_publicar_si_no_esta_solvente():
    with pytest.raises(TransicionDeBoletinInvalida):
        validar_publicacion(
            estado_actual=APROBADO, estado_aprobado=APROBADO, plazo_cumplido=True, es_solvente=False
        )


# --- Cuadro de notas institucional (RF-34) -------------------------------------------------


def test_rf34_el_cuadro_deja_en_blanco_las_unidades_sin_nota_y_promedia_solo_las_que_hay():
    from decimal import Decimal

    from apps.grading.domain.report_card import armar_fila_cuadro

    fila = armar_fila_cuadro({1: Decimal("80"), 2: Decimal("71")})

    assert fila["unidades"] == [Decimal("80"), Decimal("71"), None, None]
    assert fila["promedio"] == 76  # 75.5 redondea hacia arriba (RN-02, ADR-0003).
    assert fila["aprobado"] is True


def test_rn03_el_cuadro_marca_reprobado_con_menos_de_60_de_promedio():
    from decimal import Decimal

    from apps.grading.domain.report_card import armar_fila_cuadro

    assert armar_fila_cuadro({1: Decimal("59")})["aprobado"] is False
    assert armar_fila_cuadro({1: Decimal("60")})["aprobado"] is True


def test_rf34_una_fila_sin_ninguna_nota_no_tiene_promedio_ni_estado():
    from apps.grading.domain.report_card import armar_fila_cuadro

    fila = armar_fila_cuadro({})

    assert fila["promedio"] is None
    assert fila["aprobado"] is None


def test_rf34_el_promedio_de_unidad_es_por_columna_mas_el_general_al_final():
    from decimal import Decimal

    from apps.grading.domain.report_card import armar_fila_cuadro, promedio_de_unidades

    filas = [
        armar_fila_cuadro({1: Decimal("90"), 2: Decimal("80")}),
        armar_fila_cuadro({1: Decimal("70")}),
    ]

    assert promedio_de_unidades(filas) == [80, 80, None, None, 78]


def test_rf34_el_nivel_sale_del_grado_y_no_se_inventa_si_no_se_reconoce():
    from apps.grading.domain.report_card import nivel_del_grado

    assert nivel_del_grado("Quinto Bachillerato") == "Ciclo Diversificado"
    assert nivel_del_grado("Segundo Básico") == "Ciclo Básico"
    assert nivel_del_grado("Taller de cerámica") == ""
