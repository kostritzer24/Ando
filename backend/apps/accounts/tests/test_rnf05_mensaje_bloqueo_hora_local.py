from datetime import UTC, timedelta

import pytest
from django.utils import timezone
from django.utils.dateformat import format as formatear_fecha
from rest_framework.test import APIClient

from .factories import UserFactory


def _intentar(username):
    return APIClient().post(
        "/api/v1/auth/login/", {"username": username, "password": "Correcta-Segura-2026"}
    )


@pytest.mark.django_db
def test_rnf05_mensaje_de_bloqueo_usa_la_hora_de_guatemala_no_utc():
    hasta = timezone.now() + timedelta(minutes=15)
    UserFactory(username="bloq.hora", password="Correcta-Segura-2026", locked_until=hasta)

    detalle = str(_intentar("bloq.hora").data["detail"])

    assert timezone.localtime(hasta).strftime("%H:%M") in detalle
    assert hasta.astimezone(UTC).strftime("%H:%M") not in detalle


@pytest.mark.django_db
def test_rn16_bloqueo_de_24_horas_dice_el_dia_ademas_de_la_hora():
    hasta = timezone.now() + timedelta(hours=24)
    UserFactory(username="bloq.dia", password="Correcta-Segura-2026", locked_until=hasta)

    respuesta = _intentar("bloq.dia")

    assert respuesta.status_code == 401
    local = timezone.localtime(hasta)
    assert f"del {formatear_fecha(local, 'j')} de" in str(respuesta.data["detail"])
