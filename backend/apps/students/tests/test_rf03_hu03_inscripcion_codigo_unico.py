import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import RoleFactory, UserFactory
from apps.catalog.tests.factories import SchoolCycleFactory, SectionFactory
from apps.students.models import Enrollment, Student

from .factories import StudentFactory


@pytest.mark.django_db
def test_rf03_direccion_inscribe_un_estudiante_y_el_sistema_asigna_el_codigo():
    rol = RoleFactory(name="Dirección", permissions={"estudiantes_encargados": "editar"})
    direccion = UserFactory(role=rol)

    client = APIClient()
    client.force_authenticate(user=direccion)

    respuesta = client.post(
        "/api/v1/students/",
        {
            "first_name": "María Ximena",
            "last_name": "Pérez Tzul",
            "birth_date": "2013-05-14",
        },
        format="json",
    )

    assert respuesta.status_code == 201
    assert respuesta.data["internal_code"] == "ES001"


@pytest.mark.django_db
def test_rf03_el_codigo_interno_del_cliente_se_ignora():
    rol = RoleFactory(name="Dirección", permissions={"estudiantes_encargados": "editar"})
    direccion = UserFactory(role=rol)

    client = APIClient()
    client.force_authenticate(user=direccion)

    respuesta = client.post(
        "/api/v1/students/",
        {
            "first_name": "Juan",
            "last_name": "López",
            "birth_date": "2012-03-01",
            "internal_code": "ES999",
        },
        format="json",
    )

    assert respuesta.status_code == 201
    assert respuesta.data["internal_code"] == "ES001"


@pytest.mark.django_db
def test_rf03_docente_no_puede_inscribir_estudiantes_acceso_no_autorizado():
    rol = RoleFactory(name="Docente", permissions={"estudiantes_encargados": "ver"})
    docente = UserFactory(role=rol)

    client = APIClient()
    client.force_authenticate(user=docente)

    respuesta = client.post(
        "/api/v1/students/",
        {"first_name": "Juan", "last_name": "López", "birth_date": "2012-03-01"},
        format="json",
    )

    assert respuesta.status_code == 403


@pytest.mark.django_db
def test_hu03_no_se_puede_inscribir_dos_veces_en_el_mismo_ciclo():
    rol = RoleFactory(name="Dirección", permissions={"estudiantes_encargados": "editar"})
    direccion = UserFactory(role=rol)
    estudiante = StudentFactory()
    ciclo = SchoolCycleFactory()
    seccion_a = SectionFactory(cycle=ciclo, grade="Segundo básico", letter="A")
    seccion_b = SectionFactory(cycle=ciclo, grade="Segundo básico", letter="B")

    client = APIClient()
    client.force_authenticate(user=direccion)

    primera = client.post(
        "/api/v1/enrollments/",
        {
            "student": str(estudiante.public_id),
            "section": str(seccion_a.public_id),
            "cycle": str(ciclo.public_id),
            "enrolled_at": "2026-01-12",
        },
        format="json",
    )
    assert primera.status_code == 201

    segunda = client.post(
        "/api/v1/enrollments/",
        {
            "student": str(estudiante.public_id),
            "section": str(seccion_b.public_id),
            "cycle": str(ciclo.public_id),
            "enrolled_at": "2026-01-13",
        },
        format="json",
    )

    assert segunda.status_code == 400
    assert Enrollment.objects.filter(student=estudiante, cycle=ciclo).count() == 1


@pytest.mark.django_db
def test_hu03_el_mismo_estudiante_puede_inscribirse_en_ciclos_distintos():
    rol = RoleFactory(name="Dirección", permissions={"estudiantes_encargados": "editar"})
    direccion = UserFactory(role=rol)
    estudiante = StudentFactory()
    ciclo_uno = SchoolCycleFactory()
    ciclo_dos = SchoolCycleFactory()

    client = APIClient()
    client.force_authenticate(user=direccion)

    for ciclo in (ciclo_uno, ciclo_dos):
        seccion = SectionFactory(cycle=ciclo)
        respuesta = client.post(
            "/api/v1/enrollments/",
            {
                "student": str(estudiante.public_id),
                "section": str(seccion.public_id),
                "cycle": str(ciclo.public_id),
                "enrolled_at": "2026-01-12",
            },
            format="json",
        )
        assert respuesta.status_code == 201

    assert Student.objects.get(pk=estudiante.pk).enrollments.count() == 2
