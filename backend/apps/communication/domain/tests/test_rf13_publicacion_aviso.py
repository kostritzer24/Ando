import pytest

from apps.communication.domain.announcement import PublicacionDeAvisoInvalida, validar_publicacion


def test_rf13_aviso_para_todos_no_lleva_seccion():
    validar_publicacion(audience="todos", target_section=None, audiencia_seccion="seccion")


def test_rf13_aviso_para_seccion_necesita_elegir_cual():
    with pytest.raises(PublicacionDeAvisoInvalida):
        validar_publicacion(audience="seccion", target_section=None, audiencia_seccion="seccion")


def test_rf13_aviso_para_todos_rechaza_seccion():
    with pytest.raises(PublicacionDeAvisoInvalida):
        validar_publicacion(audience="todos", target_section=object(), audiencia_seccion="seccion")
