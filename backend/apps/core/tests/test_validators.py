import pytest
from django.core.exceptions import ValidationError

from apps.core.validators import ContrasenaComunEsValidator


def test_contrasena_comun_es_rechazada():
    with pytest.raises(ValidationError):
        ContrasenaComunEsValidator().validate("guatemala2025")


def test_contrasena_comun_es_no_distingue_mayusculas():
    with pytest.raises(ValidationError):
        ContrasenaComunEsValidator().validate("GUATEMALA2025")


def test_contrasena_poco_comun_pasa():
    ContrasenaComunEsValidator().validate("un-valor-bastante-improbable-99z")
