from apps.communication.domain.buzon import contiene_lenguaje_inapropiado


def test_rn16_detecta_palabra_inapropiada():
    assert contiene_lenguaje_inapropiado("Sos un idiota") is True


def test_rn16_no_distingue_mayusculas_ni_acentos():
    assert contiene_lenguaje_inapropiado("ESTUPIDO el profe") is True


def test_rn16_mensaje_normal_no_se_marca():
    assert contiene_lenguaje_inapropiado("Buenos días, quería consultar sobre la tarea") is False


def test_rn16_coincidencia_es_por_palabra_completa():
    """ "estupidez" no es "estupido" — el filtro no debe marcar de más."""
    assert contiene_lenguaje_inapropiado("Qué estupidez de trámite tan largo") is False


def test_rn16_detecta_letras_cambiadas_por_numeros_y_repetidas():
    """Hallazgo D-002."""
    assert contiene_lenguaje_inapropiado("put0") is True
    assert contiene_lenguaje_inapropiado("1diota") is True
    assert contiene_lenguaje_inapropiado("m13rda") is True
    assert contiene_lenguaje_inapropiado("puuuta") is True


def test_rn16_numeros_normales_no_se_marcan():
    assert contiene_lenguaje_inapropiado("La reunión es el 12 de marzo de 2026 a las 10") is False
