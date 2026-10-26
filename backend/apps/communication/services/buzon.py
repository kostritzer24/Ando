from django.db import transaction
from django.db.models import Exists, OuterRef, Q, QuerySet, Subquery
from django.utils import timezone

from apps.students.models import Enrollment, GuardianStudentLink

from ..domain.buzon import DURACION_BLOQUEO, contiene_lenguaje_inapropiado
from ..models import Conversation, ConversationRead, Message


class LenguajeInapropiado(Exception):
    """RN-16: el mensaje nunca se crea, y quien lo envió queda bloqueado."""


class CuentaBloqueada(Exception):
    """RN-16: mientras dure el bloqueo no se envía nada, aunque el token
    emitido antes del bloqueo siga siendo válido."""


class DestinatarioInvalido(Exception):
    """RF-38: la conversación necesita un vínculo activo entre el
    encargado y el estudiante, y que el estudiante esté inscrito."""


def _exigir_cuenta_libre(usuario) -> None:
    if usuario.esta_bloqueado:
        raise CuentaBloqueada("Tu cuenta está bloqueada temporalmente; no puedes enviar mensajes.")


def _bloquear(usuario) -> None:
    usuario.locked_until = timezone.now() + DURACION_BLOQUEO
    usuario.save(update_fields=["locked_until"])


def _filtrar(usuario, *textos: str) -> None:
    """RN-16 para cualquier mensaje de cualquier rol (RN-19)."""
    _exigir_cuenta_libre(usuario)
    if any(contiene_lenguaje_inapropiado(texto) for texto in textos):
        _bloquear(usuario)
        raise LenguajeInapropiado(
            "El mensaje contiene lenguaje inapropiado — no se envió y tu cuenta "
            "quedó bloqueada temporalmente."
        )


def marcar_leida(conversation: Conversation, usuario, *, hasta=None) -> None:
    ConversationRead.objects.update_or_create(
        conversation=conversation,
        user=usuario,
        defaults={"last_read_at": hasta or conversation.last_message_at},
    )


def _agregar_mensaje(conversation: Conversation, *, sender, content: str) -> Message:
    mensaje = Message.objects.create(conversation=conversation, sender=sender, content=content)
    conversation.last_message_at = mensaje.created_at
    conversation.save(update_fields=["last_message_at", "updated_at"])
    # Quien escribe ya leyó hasta su propio mensaje.
    marcar_leida(conversation, sender, hasta=mensaje.created_at)
    return mensaje


def inscripcion_activa(student) -> Enrollment | None:
    """La sección de la conversación es la del grado (no la del taller),
    igual que en Pagos."""
    return (
        Enrollment.objects.filter(student=student, is_active=True, status=Enrollment.ESTADO_ACTIVO)
        .select_related("section")
        .order_by("section__type", "-cycle__year")
        .first()
    )


def iniciar_conversacion(
    *, creada_por, guardian, student, subject: str, content: str
) -> Conversation:
    """RF-37 (la familia) y RF-38 (un docente o Dirección): la conversación
    queda amarrada a la sección activa del estudiante en este momento. El
    filtro de RN-16 va fuera de la transacción: el bloqueo tiene que
    quedar guardado aunque el mensaje se rechace."""
    _filtrar(creada_por, subject, content)
    if not GuardianStudentLink.objects.filter(
        guardian=guardian, student=student, is_active=True
    ).exists():
        raise DestinatarioInvalido("Ese encargado no está vinculado a ese estudiante.")
    inscripcion = inscripcion_activa(student)
    if inscripcion is None:
        raise DestinatarioInvalido("Ese estudiante no tiene una inscripción activa.")
    with transaction.atomic():
        conversacion = Conversation.objects.create(
            student=student,
            guardian=guardian,
            section=inscripcion.section,
            subject=subject,
            created_by=creada_por,
            last_message_at=timezone.now(),
        )
        _agregar_mensaje(conversacion, sender=creada_por, content=content)
    return conversacion


def responder(*, conversation: Conversation, sender, content: str) -> Message:
    """RF-25/RF-37: cualquier participante responde, la familia incluida."""
    _filtrar(sender, content)
    with transaction.atomic():
        conversation = Conversation.objects.select_for_update().get(pk=conversation.pk)
        return _agregar_mensaje(conversation, sender=sender, content=content)


def con_no_leido(queryset: QuerySet, usuario) -> QuerySet:
    """Anota `no_leido` (RN-19): sin lectura propia, o con un mensaje
    posterior a ella."""
    lecturas = ConversationRead.objects.filter(conversation=OuterRef("pk"), user=usuario)
    return queryset.annotate(
        leida_hasta=Subquery(lecturas.values("last_read_at")[:1]),
        no_leido=~Exists(lecturas.filter(last_read_at__gte=OuterRef("last_message_at"))),
    )


def contar_no_leidas(queryset: QuerySet, usuario) -> int:
    return con_no_leido(queryset, usuario).filter(no_leido=True).count()


def buscar_destinatarios(texto: str = "") -> list[dict]:
    """RF-38: una fila por vínculo activo encargado–alumno, con el alumno
    inscrito; se busca por el nombre de cualquiera de los dos."""
    vinculos = (
        GuardianStudentLink.objects.filter(
            is_active=True,
            guardian__is_active=True,
            student__enrollments__is_active=True,
            student__enrollments__status=Enrollment.ESTADO_ACTIVO,
        )
        .select_related("guardian", "student")
        .distinct()
        .order_by("guardian__full_name", "student__last_name", "student__first_name")
    )
    for palabra in texto.split():
        vinculos = vinculos.filter(
            Q(guardian__full_name__icontains=palabra)
            | Q(student__first_name__icontains=palabra)
            | Q(student__last_name__icontains=palabra)
        )
    return [
        {
            "guardian": vinculo.guardian.public_id,
            "student": vinculo.student.public_id,
            "guardian_name": vinculo.guardian.full_name,
            "student_name": vinculo.student.nombre_completo(),
            "label": f"{vinculo.guardian.full_name} / {vinculo.student.nombre_completo()}",
        }
        for vinculo in vinculos
    ]
