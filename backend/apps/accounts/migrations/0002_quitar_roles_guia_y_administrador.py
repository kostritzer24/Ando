from django.db import migrations

ROL_GUIA = "Docente con sección a cargo"
ROL_ADMIN = "Administrador del sistema"


def quitar_roles(apps, schema_editor):
    """Los roles "Docente con sección a cargo" y "Administrador del
    sistema" dejan de existir: quien tenía el primero pasa a "Docente"
    (con los permisos de reportes de conducta y buzón que ahora trae) y
    quien tenía el segundo pasa a "Coordinación" (solo lectura) — nunca a
    un rol con más acceso del que tenía."""
    Role = apps.get_model("accounts", "Role")
    User = apps.get_model("accounts", "User")

    docente = Role.objects.filter(name="Docente").first()
    if docente is not None:
        permisos = dict(docente.permissions)
        permisos["reportes_conducta"] = "editar"
        permisos["buzon"] = "editar"
        docente.permissions = permisos
        docente.save(update_fields=["permissions"])

    for nombre_viejo, nombre_nuevo in ((ROL_GUIA, "Docente"), (ROL_ADMIN, "Coordinación")):
        viejo = Role.objects.filter(name=nombre_viejo).first()
        if viejo is None:
            continue
        nuevo = Role.objects.filter(name=nombre_nuevo).first()
        if nuevo is None:
            # Base sin sembrar: no hay a dónde mover a nadie; se deja el rol
            # inactivo en lugar de borrarlo para no romper la clave foránea.
            if User.objects.filter(role=viejo).exists():
                viejo.is_active = False
                viejo.save(update_fields=["is_active"])
                continue
        else:
            User.objects.filter(role=viejo).update(role=nuevo)
        viejo.delete()


class Migration(migrations.Migration):
    dependencies = [("accounts", "0001_initial")]

    operations = [migrations.RunPython(quitar_roles, migrations.RunPython.noop)]
