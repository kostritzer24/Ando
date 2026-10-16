from django.db import migrations


def crear_tipo(apps, schema_editor):
    """Cierre de pensum (solo quinto bachillerato): consolidado de notas
    finales por curso y por año. Se crea con la migración para que exista
    también en las bases ya sembradas."""
    DocumentType = apps.get_model("catalog", "DocumentType")
    DocumentType.objects.get_or_create(
        template_key="cierre_pensum", defaults={"name": "Cierre de pensum", "is_active": True}
    )


class Migration(migrations.Migration):
    dependencies = [("catalog", "0003_quitar_becas_parciales")]

    operations = [migrations.RunPython(crear_tipo, migrations.RunPython.noop)]
