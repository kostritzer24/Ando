from django.utils import timezone

from ..domain.buzon import DURACION_BLOQUEO, contiene_lenguaje_inapropiado
from ..models import Message


class LenguajeInapropiado(Exception):
    """RN-16: el mensaje nunca se crea, y quien lo envió queda bloqueado."""


class CuentaBloqueada(Exception):
    """RN-16: mientras dure el bloqueo no se envía nada, aunque el token
    emitido antes del bloqueo siga siendo válido."""


def _exigir_cuenta_libre(usuario) -> None:
    if usuario.esta_bloqueado:
        raise CuentaBloqueada("Tu cuenta está bloqueada temporalmente; no puedes enviar mensajes.")


def _bloquear(usuario) -> None:
    usuario.locked_until = timezone.now() + DURACION_BLOQUEO
    usuario.save(update_fields=["locked_until"])


def enviar_mensaje(*, sender, section, subject: str, content: str) -> Message:
    """RF-25/RF-37: mensaje raíz de un hilo nuevo."""
    _exigir_cuenta_libre(sender)
    if contiene_lenguaje_inapropiado(subject) or contiene_lenguaje_inapropiado(content):
        _bloquear(sender)
        raise LenguajeInapropiado(
            "El mensaje contiene lenguaje inapropiado — no se envió y tu cuenta "
            "quedó bloqueada temporalmente."
        )
    return Message.objects.create(sender=sender, section=section, subject=subject, content=content)


def responder_mensaje(*, hilo_raiz: Message, sender, content: str) -> Message:
    """RF-25: la respuesta siempre cuelga del mensaje raíz del hilo, nunca
    de la última respuesta (sección 8: "mensajes enlazados... no una
    conversación") — y deja el hilo en `respondido`."""
    _exigir_cuenta_libre(sender)
    if contiene_lenguaje_inapropiado(content):
        _bloquear(sender)
        raise LenguajeInapropiado(
            "El mensaje contiene lenguaje inapropiado — no se envió y tu cuenta "
            "quedó bloqueada temporalmente."
        )
    respuesta = Message.objects.create(
        sender=sender, section=hilo_raiz.section, content=content, original_message=hilo_raiz
    )
    hilo_raiz.status = Message.ESTADO_RESPONDIDO
    hilo_raiz.save(update_fields=["status", "updated_at"])
    return respuesta


def marcar_leido(hilo_raiz: Message) -> None:
    if hilo_raiz.status == Message.ESTADO_ENVIADO:
        hilo_raiz.status = Message.ESTADO_LEIDO
        hilo_raiz.save(update_fields=["status", "updated_at"])
