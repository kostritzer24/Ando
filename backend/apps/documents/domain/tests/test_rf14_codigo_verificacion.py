import re

from apps.documents.domain.verification_code import generar_codigo_verificacion


def test_el_codigo_no_es_correlativo_ni_previsible():
    codigos = {generar_codigo_verificacion() for _ in range(200)}
    assert len(codigos) == 200


def test_el_codigo_tiene_un_formato_estable():
    codigo = generar_codigo_verificacion()
    assert re.fullmatch(r"[0-9A-F]{12}", codigo)
