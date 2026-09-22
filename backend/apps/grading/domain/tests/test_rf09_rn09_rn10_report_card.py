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
