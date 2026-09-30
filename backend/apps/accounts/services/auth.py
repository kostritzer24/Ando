"""Casos de uso de accounts: un caso de uso por operación, conforme a la
arquitectura por capas de la sección 12.1 del prompt maestro."""

from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.services import registrar_cambio

from ..domain.gestion_usuarios import validar_cambio_propio
from ..domain.lockout import calcular_bloqueo
from ..models import Role, User


class CredencialesInvalidas(Exception):
    """Usuario inexistente, inactivo o contraseña incorrecta. No se
    distingue el motivo en el mensaje que llega al cliente."""


class UsuarioBloqueado(Exception):
    def __init__(self, bloqueado_hasta):
        self.bloqueado_hasta = bloqueado_hasta
        super().__init__("Usuario bloqueado temporalmente.")


def iniciar_sesion(*, username: str, password: str) -> tuple[User, RefreshToken]:
    """RF-27 / sección 14.1. Aplica el bloqueo temporal creciente de RNF-05."""
    try:
        user = User.objects.select_related("role").get(username=username, is_active=True)
    except User.DoesNotExist:
        raise CredencialesInvalidas from None

    if user.esta_bloqueado:
        raise UsuarioBloqueado(user.locked_until)

    if not user.check_password(password):
        user.failed_login_attempts += 1
        bloqueo = calcular_bloqueo(user.failed_login_attempts)
        if bloqueo:
            user.locked_until = timezone.now() + bloqueo
        user.save(update_fields=["failed_login_attempts", "locked_until"])
        if bloqueo:
            raise UsuarioBloqueado(user.locked_until)
        raise CredencialesInvalidas

    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = timezone.now()
    user.save(update_fields=["failed_login_attempts", "locked_until", "last_login"])

    refresh = RefreshToken.for_user(user)
    return user, refresh


def cambiar_contrasena(*, user: User, contrasena_nueva: str) -> None:
    """RF-27 / sección 14.1: cambio obligatorio de la contraseña temporal
    en el primer ingreso (y cambio voluntario después)."""
    user.set_password(contrasena_nueva)
    user.must_change_password = False
    user.save(update_fields=["password", "must_change_password"])


def crear_usuario(
    *,
    creado_por: User,
    username: str,
    role: Role,
    contrasena_temporal: str,
    **datos,
) -> User:
    """RF-01: crear usuarios y asignarles un rol. Sin registro libre — solo
    la administración crea cuentas (RN-14)."""
    user = User.objects.create_user(
        username=username,
        password=contrasena_temporal,
        role=role,
        must_change_password=True,
        **datos,
    )
    registrar_cambio(
        usuario=creado_por,
        entidad_nombre="accounts.User",
        entidad_id=user.id,
        accion="crear",
        valor_nuevo={"username": user.username, "role": role.name},
    )
    return user


def restablecer_contrasena(*, restablecido_por: User, user: User, contrasena_temporal: str) -> None:
    """Restablecimiento gestionado por administración, no por correo
    automático (sección 14.1: muchas familias no manejan correo activo)."""
    user.set_password(contrasena_temporal)
    user.must_change_password = True
    user.failed_login_attempts = 0
    user.locked_until = None
    user.save(
        update_fields=[
            "password",
            "must_change_password",
            "failed_login_attempts",
            "locked_until",
        ]
    )
    registrar_cambio(
        usuario=restablecido_por,
        entidad_nombre="accounts.User",
        entidad_id=user.id,
        accion="actualizar",
        valor_nuevo={"accion": "restablecer_contrasena"},
    )


CAMPOS_EDITABLES = ("first_name", "last_name", "email", "role", "is_active")


def actualizar_usuario(*, actualizado_por: User, user: User, **cambios) -> User:
    """RF-01: editar nombre, correo y rol de una cuenta, o activarla y
    desactivarla. Nunca se borra (baja lógica con `is_active`): la cuenta
    queda en la bitácora de todo lo que hizo. Deja registro en la bitácora
    con el valor anterior y el nuevo de lo que cambió."""
    cambios = {campo: valor for campo, valor in cambios.items() if campo in CAMPOS_EDITABLES}
    validar_cambio_propio(
        es_la_misma_cuenta=user.pk == actualizado_por.pk,
        desactiva=cambios.get("is_active") is False,
        cambia_rol="role" in cambios and cambios["role"] != user.role,
    )

    def legible(campo, valor):
        return valor.name if campo == "role" and valor is not None else valor

    anterior, nuevo = {}, {}
    for campo, valor in cambios.items():
        if getattr(user, campo) != valor:
            anterior[campo] = legible(campo, getattr(user, campo))
            nuevo[campo] = legible(campo, valor)
            setattr(user, campo, valor)
    if not nuevo:
        return user

    user.save(update_fields=list(nuevo))
    registrar_cambio(
        usuario=actualizado_por,
        entidad_nombre="accounts.User",
        entidad_id=user.id,
        accion="actualizar",
        valor_anterior=anterior,
        valor_nuevo=nuevo,
    )
    return user
