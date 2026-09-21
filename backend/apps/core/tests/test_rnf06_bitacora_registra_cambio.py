import pytest

from apps.accounts.services import crear_usuario
from apps.accounts.tests.factories import RoleFactory, UserFactory
from apps.core.models import AuditLog
from apps.core.services import registrar_cambio


@pytest.mark.django_db
def test_rnf06_registrar_cambio_crea_un_registro_de_bitacora():
    usuario = UserFactory()

    registro = registrar_cambio(
        usuario=usuario,
        entidad_nombre="grading.Grade",
        entidad_id=42,
        accion=AuditLog.ACCION_ACTUALIZAR,
        valor_anterior={"punteo_real": 70},
        valor_nuevo={"punteo_real": 80},
    )

    guardado = AuditLog.objects.get(pk=registro.pk)
    assert guardado.user_id == usuario.id
    assert guardado.entity_name == "grading.Grade"
    assert guardado.entity_id == 42
    assert guardado.action == AuditLog.ACCION_ACTUALIZAR
    assert guardado.old_value == {"punteo_real": 70}
    assert guardado.new_value == {"punteo_real": 80}


@pytest.mark.django_db
def test_rnf06_crear_usuario_deja_rastro_en_la_bitacora():
    administrador = UserFactory()
    rol_nuevo = RoleFactory()

    usuario_creado = crear_usuario(
        creado_por=administrador,
        username="prueba.bitacora",
        role=rol_nuevo,
        contrasena_temporal="Temporal-Segura-2026",
    )

    assert AuditLog.objects.filter(
        entity_name="accounts.User",
        entity_id=usuario_creado.id,
        action=AuditLog.ACCION_CREAR,
        user=administrador,
    ).exists()


@pytest.mark.django_db
def test_rnf06_bitacora_no_se_modifica_una_vez_creada():
    """De solo escritura (ADR-0004): no se expone ningún campo editable
    salvo por un registro nuevo."""
    usuario = UserFactory()
    registrar_cambio(
        usuario=usuario,
        entidad_nombre="attendance.Attendance",
        entidad_id=1,
        accion=AuditLog.ACCION_CREAR,
    )
    campos = {f.name for f in AuditLog._meta.get_fields()}
    assert "updated_at" not in campos
