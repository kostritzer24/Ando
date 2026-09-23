import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import RoleFactory, UserFactory

CASOS = [
    ("/api/v1/courses/", {"name": "Matemática", "type": "academico"}),
    ("/api/v1/activity-types/", {"name": "Prueba corta", "counts_as_short_quiz": True}),
    ("/api/v1/justification-types/", {"name": "Constancia médica", "requires_document": True}),
    (
        "/api/v1/document-types/",
        {"name": "Constancia de estudio", "template_key": "constancia_estudio"},
    ),
    (
        "/api/v1/scholarships/",
        {"name": "Beca completa", "description": "Cubre el 100% de la mensualidad."},
    ),
    (
        "/api/v1/conduct-rule-articles/",
        {
            "chapter": "CAPÍTULO I: RESPETO Y DIGNIDAD",
            "code": "Art. 4",
            "description": "Falta de respeto",
        },
    ),
]


@pytest.mark.django_db
@pytest.mark.parametrize("ruta,payload", CASOS)
def test_rf02_direccion_administra_cada_catalogo(ruta, payload):
    # "asistencia", "notas" y "reportes_conducta" hacen falta acá porque
    # /justification-types/, /activity-types/ y /conduct-rule-articles/
    # son la excepción entre los 8 catálogos (ver JustificationTypeViewSet,
    # ActivityTypeViewSet y ConductRuleArticleViewSet): leerlos pasa por
    # esas áreas, no por "datos_maestros" — administrar el catálogo (lo
    # que esta prueba ejercita) sigue siendo igual para los 5 restantes.
    rol = RoleFactory(
        name="Dirección",
        permissions={
            "datos_maestros": "editar",
            "asistencia": "editar",
            "notas": "editar",
            "reportes_conducta": "editar",
        },
    )
    direccion = UserFactory(role=rol)

    client = APIClient()
    client.force_authenticate(user=direccion)

    respuesta_crear = client.post(ruta, payload, format="json")
    assert respuesta_crear.status_code == 201

    respuesta_listar = client.get(ruta)
    assert respuesta_listar.status_code == 200
    assert respuesta_listar.data["count"] == 1


@pytest.mark.django_db
@pytest.mark.parametrize("ruta,payload", CASOS)
def test_rf02_tallerista_no_puede_editar_ningun_catalogo(ruta, payload):
    rol = RoleFactory(name="Tallerista", permissions={"datos_maestros": "sin_acceso"})
    tallerista = UserFactory(role=rol)

    client = APIClient()
    client.force_authenticate(user=tallerista)

    respuesta = client.post(ruta, payload, format="json")
    assert respuesta.status_code == 403
