import pytest

from apps.accounts.domain.lockout import calcular_bloqueo


@pytest.mark.parametrize("intentos", [0, 1, 4])
def test_rnf05_sin_bloqueo_antes_del_umbral(intentos):
    assert calcular_bloqueo(intentos) is None


@pytest.mark.parametrize(
    "intentos,minutos_esperados",
    [(5, 1), (6, 5), (7, 15)],
)
def test_rnf05_bloqueo_creciente(intentos, minutos_esperados):
    bloqueo = calcular_bloqueo(intentos)
    assert bloqueo is not None
    assert bloqueo.total_seconds() == minutos_esperados * 60


def test_rnf05_bloqueo_se_limita_a_una_hora_maximo():
    assert calcular_bloqueo(50).total_seconds() == 60 * 60
