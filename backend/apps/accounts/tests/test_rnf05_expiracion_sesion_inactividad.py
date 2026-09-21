from datetime import timedelta

import pytest
from django.conf import settings
from django.utils import timezone
from rest_framework.test import APIRequestFactory
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.tokens import AccessToken

from .factories import UserFactory


def test_rnf05_token_de_acceso_dura_15_minutos():
    assert settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"] == timedelta(minutes=15)


@pytest.mark.django_db
def test_rnf05_token_expirado_no_autentica():
    usuario = UserFactory()
    token = AccessToken.for_user(usuario)
    token.set_exp(from_time=timezone.now() - timedelta(minutes=20), lifetime=timedelta(minutes=15))

    request = APIRequestFactory().get("/", HTTP_AUTHORIZATION=f"Bearer {token}")
    with pytest.raises(InvalidToken):
        JWTAuthentication().authenticate(request)
