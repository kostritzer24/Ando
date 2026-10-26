import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """ADR-0008: después de 0005 todo mensaje tiene conversación; la
    sección, el asunto, el mensaje original y el estado pasan a la
    conversación y a la lectura por usuario."""

    dependencies = [("communication", "0005_mensajes_a_conversaciones")]

    operations = [
        migrations.RemoveField(model_name="message", name="original_message"),
        migrations.RemoveField(model_name="message", name="section"),
        migrations.RemoveField(model_name="message", name="status"),
        migrations.RemoveField(model_name="message", name="subject"),
        migrations.AlterField(
            model_name="message",
            name="conversation",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="messages",
                to="communication.conversation",
                verbose_name="conversación",
            ),
        ),
    ]
