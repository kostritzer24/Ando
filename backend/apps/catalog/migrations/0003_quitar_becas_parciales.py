from django.db import migrations


def desactivar_becas_parciales(apps, schema_editor):
    """La beca solo puede ser completa o no haber beca: las becas parciales
    dejan de ofrecerse (se desactivan, no se borran, porque una inscripción
    antigua pudo haberla usado)."""
    Scholarship = apps.get_model("catalog", "Scholarship")
    Scholarship.objects.filter(name__icontains="parcial").update(is_active=False)


class Migration(migrations.Migration):
    dependencies = [("catalog", "0002_alter_section_homeroom_teacher")]

    operations = [migrations.RunPython(desactivar_becas_parciales, migrations.RunPython.noop)]
