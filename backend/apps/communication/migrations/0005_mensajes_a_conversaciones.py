from django.db import migrations


class BuzonSinResolver(Exception):
    pass


def _estudiante_del_hilo(raiz, Student):
    """El mensaje raíz solo guardaba la sección: el estudiante es el
    vinculado al encargado que escribió con inscripción en esa sección (de
    preferencia activa; si son varios, el primero por nombre)."""
    candidatos = Student.objects.filter(
        guardian_links__guardian__user_id=raiz.sender_id,
        enrollments__section_id=raiz.section_id,
    ).distinct()
    activos = candidatos.filter(
        guardian_links__is_active=True, enrollments__is_active=True
    ).order_by("last_name", "first_name", "id")
    return activos.first() or candidatos.order_by("last_name", "first_name", "id").first()


def mensajes_a_conversaciones(apps, schema_editor):
    """ADR-0008: cada mensaje raíz pasa a ser una conversación; la raíz y
    sus respuestas se cuelgan de ella sin recrearse (conservan `public_id`,
    fecha y remitente). Del estado viejo solo se traduce lo atribuible:
    cada remitente leyó la conversación hasta su último mensaje. Un
    "leído" sin respuesta no dice quién lo leyó y queda sin leer."""
    Message = apps.get_model("communication", "Message")
    Conversation = apps.get_model("communication", "Conversation")
    ConversationRead = apps.get_model("communication", "ConversationRead")
    Guardian = apps.get_model("students", "Guardian")
    Student = apps.get_model("students", "Student")

    sin_resolver = []
    for raiz in Message.objects.filter(original_message__isnull=True).order_by("id"):
        guardian = Guardian.objects.filter(user_id=raiz.sender_id).first()
        student = _estudiante_del_hilo(raiz, Student) if guardian else None
        if guardian is None or student is None:
            sin_resolver.append(raiz.id)
            continue

        mensajes = list(
            Message.objects.filter(id=raiz.id) | Message.objects.filter(original_message_id=raiz.id)
        )
        ultimo = max(m.created_at for m in mensajes)
        conversacion = Conversation.objects.create(
            student=student,
            guardian=guardian,
            section_id=raiz.section_id,
            subject=raiz.subject or "(sin asunto)",
            created_by_id=raiz.sender_id,
            last_message_at=ultimo,
            is_active=raiz.is_active,
        )
        # `created_at` es auto_now_add: se corrige después para que la
        # conversación conserve la fecha del mensaje que la abrió.
        Conversation.objects.filter(id=conversacion.id).update(created_at=raiz.created_at)
        Message.objects.filter(id__in=[m.id for m in mensajes]).update(
            conversation_id=conversacion.id
        )

        leido_hasta = {}
        for mensaje in mensajes:
            previo = leido_hasta.get(mensaje.sender_id)
            if previo is None or mensaje.created_at > previo:
                leido_hasta[mensaje.sender_id] = mensaje.created_at
        ConversationRead.objects.bulk_create(
            ConversationRead(conversation=conversacion, user_id=usuario, last_read_at=fecha)
            for usuario, fecha in leido_hasta.items()
        )

    if sin_resolver:
        raise BuzonSinResolver(
            "No se pudo saber de qué estudiante o encargado son los mensajes de buzón con id "
            f"{sin_resolver}: el remitente no es un encargado con un estudiante inscrito en esa "
            "sección. Corrígelos a mano (vínculo o inscripción) y vuelve a correr la migración."
        )


def sin_reversa_con_datos(apps, schema_editor):
    """No hay forma confiable de partir una conversación de dos vías en
    hilos de una sola vía (y la migración siguiente borró la sección y el
    asunto de cada mensaje). Solo se permite revertir sin conversaciones,
    lo que sirve para bases vacías y para la prueba de esta migración."""
    if apps.get_model("communication", "Conversation").objects.exists():
        raise BuzonSinResolver("El buzón ya tiene conversaciones; esta migración no se revierte.")


class Migration(migrations.Migration):
    dependencies = [
        ("communication", "0004_conversaciones"),
        ("students", "0002_permitir_seccion_academica_y_taller_a_la_vez"),
    ]

    operations = [migrations.RunPython(mensajes_a_conversaciones, sin_reversa_con_datos)]
