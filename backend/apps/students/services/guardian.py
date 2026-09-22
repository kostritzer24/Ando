from ..models import Guardian

ROL_ENCARGADO = "Padre de familia"


class RolDeUsuarioInvalido(Exception):
    pass


def crear_encargado(
    *, user, full_name: str, phone: str = "", messaging_number: str = "", occupation: str = ""
) -> Guardian:
    if user.role.name != ROL_ENCARGADO:
        raise RolDeUsuarioInvalido(f"El usuario debe tener el rol '{ROL_ENCARGADO}'.")
    return Guardian.objects.create(
        user=user,
        full_name=full_name,
        phone=phone,
        messaging_number=messaging_number,
        occupation=occupation,
    )
