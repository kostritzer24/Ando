from ..models import Guardian, GuardianStudentLink, Student


class VinculoYaExiste(Exception):
    pass


def vincular_encargado_estudiante(
    *, guardian: Guardian, student: Student, relationship: str, is_primary: bool = False
) -> GuardianStudentLink:
    """RF-04. Un estudiante puede tener más de un encargado (ADR-0002):
    esto solo crea un vínculo más, nunca reemplaza uno existente."""
    if GuardianStudentLink.objects.filter(
        guardian=guardian, student=student, is_active=True
    ).exists():
        raise VinculoYaExiste("Este encargado ya está vinculado a este estudiante.")
    return GuardianStudentLink.objects.create(
        guardian=guardian, student=student, relationship=relationship, is_primary=is_primary
    )


def desvincular_encargado_estudiante(vinculo: GuardianStudentLink) -> None:
    """Baja lógica (HU-02): el vínculo se desactiva, no se borra."""
    vinculo.is_active = False
    vinculo.save(update_fields=["is_active", "updated_at"])
