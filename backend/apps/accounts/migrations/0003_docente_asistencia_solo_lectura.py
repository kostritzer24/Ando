from django.db import migrations


def docente_solo_ve_asistencia(apps, schema_editor):
    """Ronda de pruebas del director: el Docente solo consulta la asistencia
    que marcó Dirección; marcarla queda para Dirección y para el Tallerista
    (en sus talleres)."""
    Role = apps.get_model("accounts", "Role")
    docente = Role.objects.filter(name="Docente").first()
    if docente is not None:
        permisos = dict(docente.permissions)
        permisos["asistencia"] = "ver"
        docente.permissions = permisos
        docente.save(update_fields=["permissions"])


class Migration(migrations.Migration):
    dependencies = [("accounts", "0002_quitar_roles_guia_y_administrador")]

    operations = [migrations.RunPython(docente_solo_ve_asistencia, migrations.RunPython.noop)]
