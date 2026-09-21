import pytest
from django.utils import timezone

from apps.accounts.domain.lockout import UMBRAL_BLOQUEO
from apps.accounts.services import CredencialesInvalidas, UsuarioBloqueado, iniciar_sesion

from .factories import UserFactory


@pytest.mark.django_db
def test_rnf05_bloquea_despues_del_umbral_de_intentos_fallidos():
    UserFactory(username="con.bloqueo", password="Correcta-Segura-2026")

    for _ in range(UMBRAL_BLOQUEO - 1):
        with pytest.raises(CredencialesInvalidas):
            iniciar_sesion(username="con.bloqueo", password="incorrecta")

    with pytest.raises(UsuarioBloqueado) as excinfo:
        iniciar_sesion(username="con.bloqueo", password="incorrecta")

    assert excinfo.value.bloqueado_hasta > timezone.now()


@pytest.mark.django_db
def test_rnf05_contrasena_correcta_no_pasa_mientras_esta_bloqueado():
    UserFactory(username="con.bloqueo.2", password="Correcta-Segura-2026")
    for _ in range(UMBRAL_BLOQUEO):
        try:
            iniciar_sesion(username="con.bloqueo.2", password="incorrecta")
        except (CredencialesInvalidas, UsuarioBloqueado):
            pass

    with pytest.raises(UsuarioBloqueado):
        iniciar_sesion(username="con.bloqueo.2", password="Correcta-Segura-2026")


@pytest.mark.django_db
def test_rnf05_inicio_de_sesion_correcto_reinicia_los_intentos():
    usuario = UserFactory(username="normal", password="Correcta-Segura-2026")

    with pytest.raises(CredencialesInvalidas):
        iniciar_sesion(username="normal", password="incorrecta")

    iniciar_sesion(username="normal", password="Correcta-Segura-2026")

    usuario.refresh_from_db()
    assert usuario.failed_login_attempts == 0
    assert usuario.locked_until is None
