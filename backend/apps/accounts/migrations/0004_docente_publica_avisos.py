from django.db import migrations


def docente_publica_avisos(apps, schema_editor):
    """Capacitación docente (RF-13 revisado, RN-18): cualquier Docente
    publica avisos; solo edita y retira los suyos (eso lo valida
    `communication/domain/announcement.py`, no el permiso del área). Los
    roles ya sembrados en producción no releen `seed_fase3.py`."""
    Role = apps.get_model("accounts", "Role")
    docente = Role.objects.filter(name="Docente").first()
    if docente is not None:
        permisos = dict(docente.permissions)
        permisos["avisos"] = "editar"
        docente.permissions = permisos
        docente.save(update_fields=["permissions"])


def docente_solo_ve_avisos(apps, schema_editor):
    Role = apps.get_model("accounts", "Role")
    docente = Role.objects.filter(name="Docente").first()
    if docente is not None:
        permisos = dict(docente.permissions)
        permisos["avisos"] = "ver"
        docente.permissions = permisos
        docente.save(update_fields=["permissions"])


class Migration(migrations.Migration):
    dependencies = [("accounts", "0003_docente_asistencia_solo_lectura")]

    operations = [migrations.RunPython(docente_publica_avisos, docente_solo_ve_avisos)]
