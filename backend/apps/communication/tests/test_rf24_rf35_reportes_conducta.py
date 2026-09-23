import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import RoleFactory, UserFactory
from apps.catalog.models import ConductRuleArticle
from apps.catalog.tests.factories import SectionFactory
from apps.communication.models import ConductReport
from apps.students.services.link import vincular_encargado_estudiante
from apps.students.tests.factories import EnrollmentFactory, GuardianFactory, StudentFactory

pytestmark = pytest.mark.django_db


def _direccion():
    rol = RoleFactory(name="Dirección", permissions={"reportes_conducta": "editar"})
    return UserFactory(role=rol)


def _guia_de(seccion):
    rol = RoleFactory(
        name="Docente con sección a cargo", permissions={"reportes_conducta": "editar"}
    )
    guia = UserFactory(role=rol)
    seccion.homeroom_teacher = guia
    seccion.save(update_fields=["homeroom_teacher"])
    return guia


_DATOS_BASE = {
    "report_date": "2026-03-10",
    "severity": "leve",
    "incident_description": "Interrumpió la clase repetidamente.",
    "immediate_actions": "Se conversó con el estudiante.",
    "sanction_type": "llamado_verbal",
    "commitments": "Se compromete a levantar la mano antes de hablar.",
}


def test_rf24_el_maestro_guia_registra_un_reporte_de_su_seccion():
    seccion = SectionFactory()
    guia = _guia_de(seccion)
    inscripcion = EnrollmentFactory(section=seccion, cycle=seccion.cycle)

    client = APIClient()
    client.force_authenticate(user=guia)
    respuesta = client.post(
        "/api/v1/conduct-reports/", {**_DATOS_BASE, "enrollment": str(inscripcion.public_id)}
    )

    assert respuesta.status_code == 201
    assert respuesta.data["guide_teacher"] == guia.username
    assert respuesta.data["direction_member"] is None


def test_rf24_direccion_registra_un_reporte_y_queda_como_miembro_de_direccion():
    seccion = SectionFactory()
    _guia_de(seccion)
    inscripcion = EnrollmentFactory(section=seccion, cycle=seccion.cycle)
    dir_user = _direccion()

    client = APIClient()
    client.force_authenticate(user=dir_user)
    respuesta = client.post(
        "/api/v1/conduct-reports/", {**_DATOS_BASE, "enrollment": str(inscripcion.public_id)}
    )

    assert respuesta.status_code == 201
    assert respuesta.data["direction_member"] == dir_user.username


def test_rf24_un_maestro_guia_no_puede_registrar_reportes_de_otra_seccion():
    seccion_ajena = SectionFactory()
    _guia_de(seccion_ajena)
    otra_seccion = SectionFactory()
    guia_ajeno = _guia_de(otra_seccion)
    inscripcion = EnrollmentFactory(section=seccion_ajena, cycle=seccion_ajena.cycle)

    client = APIClient()
    client.force_authenticate(user=guia_ajeno)
    respuesta = client.post(
        "/api/v1/conduct-reports/", {**_DATOS_BASE, "enrollment": str(inscripcion.public_id)}
    )

    assert respuesta.status_code == 403


def test_rf24_marca_articulos_del_catalogo():
    seccion = SectionFactory()
    guia = _guia_de(seccion)
    inscripcion = EnrollmentFactory(section=seccion, cycle=seccion.cycle)
    articulo = ConductRuleArticle.objects.create(
        chapter="CAPÍTULO I", code="Art. 4", description="Falta de respeto"
    )

    client = APIClient()
    client.force_authenticate(user=guia)
    respuesta = client.post(
        "/api/v1/conduct-reports/",
        {
            **_DATOS_BASE,
            "enrollment": str(inscripcion.public_id),
            "article_ids": [str(articulo.public_id)],
        },
    )

    assert respuesta.status_code == 201
    assert respuesta.data["articles"] == ["Falta de respeto"]


def test_rf35_la_familia_solo_ve_los_reportes_de_su_propio_hijo():
    seccion = SectionFactory()
    guia = _guia_de(seccion)
    hijo = StudentFactory()
    ajeno = StudentFactory()
    inscripcion_hijo = EnrollmentFactory(student=hijo, section=seccion, cycle=seccion.cycle)
    EnrollmentFactory(student=ajeno, section=seccion, cycle=seccion.cycle)

    ConductReport.objects.create(
        enrollment=inscripcion_hijo,
        guide_teacher=guia,
        report_date="2026-03-10",
        severity="leve",
        incident_description="...",
        immediate_actions="...",
        sanction_type="llamado_verbal",
        commitments="...",
    )
    ConductReport.objects.create(
        enrollment=EnrollmentFactory(student=ajeno, section=SectionFactory()),
        guide_teacher=guia,
        report_date="2026-03-10",
        severity="leve",
        incident_description="...",
        immediate_actions="...",
        sanction_type="llamado_verbal",
        commitments="...",
    )

    rol_familia = RoleFactory(name="Padre de familia", permissions={"reportes_conducta": "ver"})
    usuario_familia = UserFactory(role=rol_familia)
    encargado = GuardianFactory(user=usuario_familia)
    vincular_encargado_estudiante(guardian=encargado, student=hijo, relationship="Madre")

    client = APIClient()
    client.force_authenticate(user=usuario_familia)
    respuesta = client.get("/api/v1/conduct-reports/")

    assert respuesta.data["count"] == 1


def test_rf24_descarga_el_pdf_del_reporte():
    seccion = SectionFactory()
    guia = _guia_de(seccion)
    inscripcion = EnrollmentFactory(section=seccion, cycle=seccion.cycle)
    reporte = ConductReport.objects.create(
        enrollment=inscripcion,
        guide_teacher=guia,
        report_date="2026-03-10",
        severity="grave",
        incident_description="...",
        immediate_actions="...",
        sanction_type="suspension_clases",
        sanction_detail="Dos días.",
        commitments="...",
    )

    client = APIClient()
    client.force_authenticate(user=guia)
    respuesta = client.get(f"/api/v1/conduct-reports/{reporte.public_id}/download/")

    assert respuesta.status_code == 200
    assert respuesta["Content-Type"] == "application/pdf"
    assert respuesta.content[:4] == b"%PDF"
