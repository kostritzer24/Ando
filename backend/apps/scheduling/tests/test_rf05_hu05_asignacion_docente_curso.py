import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import RoleFactory, UserFactory
from apps.catalog.models import Course
from apps.catalog.tests.factories import SchoolCycleFactory, SectionFactory
from apps.scheduling.models import TeacherAssignment


@pytest.mark.django_db
def test_rf05_direccion_asigna_un_docente_a_un_curso_academico():
    rol_direccion = RoleFactory(name="Dirección", permissions={"horarios_calendario": "editar"})
    direccion = UserFactory(role=rol_direccion)
    rol_docente = RoleFactory(name="Docente")
    docente = UserFactory(role=rol_docente)
    ciclo = SchoolCycleFactory()
    seccion = SectionFactory(cycle=ciclo, type="academica")
    curso = Course.objects.create(name="Matemática", type=Course.TIPO_ACADEMICO)

    client = APIClient()
    client.force_authenticate(user=direccion)

    respuesta = client.post(
        "/api/v1/assignments/",
        {
            "teacher": str(docente.public_id),
            "course": str(curso.public_id),
            "section": str(seccion.public_id),
            "cycle": str(ciclo.public_id),
        },
        format="json",
    )

    assert respuesta.status_code == 201
    assert TeacherAssignment.objects.filter(teacher=docente, course=curso, section=seccion).exists()


@pytest.mark.django_db
def test_adr0001_no_se_puede_asignar_un_curso_academico_a_una_seccion_de_taller():
    rol_direccion = RoleFactory(name="Dirección", permissions={"horarios_calendario": "editar"})
    direccion = UserFactory(role=rol_direccion)
    rol_docente = RoleFactory(name="Docente")
    docente = UserFactory(role=rol_docente)
    ciclo = SchoolCycleFactory()
    seccion_taller = SectionFactory(cycle=ciclo, type="taller", grade="Taller de panadería")
    curso = Course.objects.create(name="Matemática", type=Course.TIPO_ACADEMICO)

    client = APIClient()
    client.force_authenticate(user=direccion)

    respuesta = client.post(
        "/api/v1/assignments/",
        {
            "teacher": str(docente.public_id),
            "course": str(curso.public_id),
            "section": str(seccion_taller.public_id),
            "cycle": str(ciclo.public_id),
        },
        format="json",
    )

    assert respuesta.status_code == 400
    assert not TeacherAssignment.objects.exists()


@pytest.mark.django_db
def test_rf05_un_tallerista_no_puede_quedar_asignado_a_un_curso_academico():
    rol_direccion = RoleFactory(name="Dirección", permissions={"horarios_calendario": "editar"})
    direccion = UserFactory(role=rol_direccion)
    rol_tallerista = RoleFactory(name="Tallerista")
    tallerista = UserFactory(role=rol_tallerista)
    ciclo = SchoolCycleFactory()
    seccion = SectionFactory(cycle=ciclo, type="academica")
    curso = Course.objects.create(name="Matemática", type=Course.TIPO_ACADEMICO)

    client = APIClient()
    client.force_authenticate(user=direccion)

    respuesta = client.post(
        "/api/v1/assignments/",
        {
            "teacher": str(tallerista.public_id),
            "course": str(curso.public_id),
            "section": str(seccion.public_id),
            "cycle": str(ciclo.public_id),
        },
        format="json",
    )

    assert respuesta.status_code == 400


@pytest.mark.django_db
def test_rf05_docente_no_puede_crear_asignaciones_ni_siquiera_para_si_mismo_acceso_no_autorizado():
    """`docs/api.md` documenta `/assignments/` como `DIR (E)` únicamente:
    un docente tiene 'editar' en el área horarios_calendario para su
    propio horario (Fase 8), pero eso no le alcanza para decidir qué
    curso da — esa decisión es exclusiva de Dirección."""
    rol_docente = RoleFactory(name="Docente", permissions={"horarios_calendario": "editar"})
    docente = UserFactory(role=rol_docente)
    ciclo = SchoolCycleFactory()
    seccion = SectionFactory(cycle=ciclo, type="academica")
    curso = Course.objects.create(name="Matemática", type=Course.TIPO_ACADEMICO)

    client = APIClient()
    client.force_authenticate(user=docente)

    respuesta = client.post(
        "/api/v1/assignments/",
        {
            "teacher": str(docente.public_id),
            "course": str(curso.public_id),
            "section": str(seccion.public_id),
            "cycle": str(ciclo.public_id),
        },
        format="json",
    )

    assert respuesta.status_code == 403
    assert not TeacherAssignment.objects.exists()


@pytest.mark.django_db
def test_docente_solo_ve_sus_propias_asignaciones():
    rol_docente = RoleFactory(name="Docente", permissions={"horarios_calendario": "ver"})
    docente_uno = UserFactory(role=rol_docente)
    docente_dos = UserFactory(role=rol_docente)
    ciclo = SchoolCycleFactory()
    seccion = SectionFactory(cycle=ciclo, type="academica")
    curso = Course.objects.create(name="Matemática", type=Course.TIPO_ACADEMICO)

    TeacherAssignment.objects.create(
        teacher=docente_uno, course=curso, section=seccion, cycle=ciclo
    )
    TeacherAssignment.objects.create(
        teacher=docente_dos, course=curso, section=seccion, cycle=ciclo
    )

    client = APIClient()
    client.force_authenticate(user=docente_uno)

    respuesta = client.get("/api/v1/assignments/")

    assert respuesta.data["count"] == 1
    assert respuesta.data["results"][0]["teacher"] == docente_uno.public_id


@pytest.mark.django_db
def test_un_docente_ve_el_grado_y_curso_de_su_propia_asignacion_sin_pasar_por_el_catalogo():
    """`/sections/` y `/courses/` viven detrás del área "datos_maestros",
    a la que un docente no llega (docs/permisos-roles.md) — pero sí
    necesita saber el grado/letra de su sección y el nombre de su curso
    para las pantallas operativas (asistencia, notas)."""
    rol_docente = RoleFactory(name="Docente", permissions={"horarios_calendario": "ver"})
    docente = UserFactory(role=rol_docente)
    ciclo = SchoolCycleFactory()
    seccion = SectionFactory(cycle=ciclo, type="academica", grade="Segundo básico", letter="")
    curso = Course.objects.create(name="Matemática", type=Course.TIPO_ACADEMICO)
    TeacherAssignment.objects.create(teacher=docente, course=curso, section=seccion, cycle=ciclo)

    client = APIClient()
    client.force_authenticate(user=docente)

    respuesta = client.get("/api/v1/assignments/")

    fila = respuesta.data["results"][0]
    assert fila["section_grade"] == "Segundo básico"
    assert fila["section_type"] == "academica"
    assert fila["course_name"] == "Matemática"


@pytest.mark.django_db
def test_rf05_editar_una_asignacion_vuelve_a_validar_el_rol_del_docente():
    """Hallazgo B-020: un PATCH dejaba a un Tallerista en un curso académico."""
    direccion = UserFactory(
        role=RoleFactory(name="Dirección", permissions={"horarios_calendario": "editar"})
    )
    docente = UserFactory(role=RoleFactory(name="Docente"))
    tallerista = UserFactory(role=RoleFactory(name="Tallerista"))
    ciclo = SchoolCycleFactory()
    seccion = SectionFactory(cycle=ciclo, type="academica")
    curso = Course.objects.create(name="Matemática", type=Course.TIPO_ACADEMICO)
    asignacion = TeacherAssignment.objects.create(
        teacher=docente, course=curso, section=seccion, cycle=ciclo
    )
    client = APIClient()
    client.force_authenticate(user=direccion)

    respuesta = client.patch(
        f"/api/v1/assignments/{asignacion.public_id}/",
        {"teacher": str(tallerista.public_id)},
        format="json",
    )

    assert respuesta.status_code == 400
    asignacion.refresh_from_db()
    assert asignacion.teacher == docente
