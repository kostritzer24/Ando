"""
Semilla mínima de la Fase 3: los 8 roles de docs/permisos-roles.md con su
matriz de permisos, más un usuario ficticio por rol para poder probar
inicio de sesión y permisos de punta a punta. No es el comando de
demostración completo de la sección 16 (ese llega cuando existan más
módulos) — ver docs/fase-3-cimientos-plan.md, sección 8.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import Role, User

# Mapa exacto de docs/permisos-roles.md. "V"→ver, "E"→editar, "S"→sin_acceso.
_V, _E, _S = "ver", "editar", "sin_acceso"

_MATRIZ: dict[str, dict[str, str]] = {
    "Dirección": {
        "usuarios_roles": _E,
        "datos_maestros": _E,
        "estudiantes_encargados": _E,
        "datos_sensibles": _E,
        "horarios_calendario": _E,
        "asistencia": _E,
        "notas": _E,
        "modificacion_notas": _E,
        "pagos_solvencia": _E,
        "documentos": _E,
        "avisos": _E,
        "reportes_conducta": _E,
        "buzon": _E,
        "reportes_institucionales": _E,
        "bitacora_registro_acceso": _V,
    },
    "Coordinación": {
        "usuarios_roles": _S,
        "datos_maestros": _V,
        "estudiantes_encargados": _V,
        "datos_sensibles": _S,
        "horarios_calendario": _V,
        "asistencia": _V,
        "notas": _V,
        "modificacion_notas": _S,
        "pagos_solvencia": _V,
        "documentos": _V,
        "avisos": _V,
        "reportes_conducta": _V,
        "buzon": _S,
        "reportes_institucionales": _V,
        "bitacora_registro_acceso": _S,
    },
    "Encargado de pagos": {
        "usuarios_roles": _S,
        "datos_maestros": _S,
        "estudiantes_encargados": _V,
        "datos_sensibles": _S,
        "horarios_calendario": _S,
        "asistencia": _S,
        "notas": _S,
        "modificacion_notas": _S,
        "pagos_solvencia": _E,
        "documentos": _E,
        "avisos": _S,
        "reportes_conducta": _S,
        "buzon": _S,
        "reportes_institucionales": _S,
        "bitacora_registro_acceso": _S,
    },
    "Docente": {
        "usuarios_roles": _S,
        "datos_maestros": _S,
        "estudiantes_encargados": _V,
        "datos_sensibles": _S,
        "horarios_calendario": _E,
        "asistencia": _E,
        "notas": _E,
        "modificacion_notas": _S,
        "pagos_solvencia": _S,
        "documentos": _S,
        "avisos": _V,
        "reportes_conducta": _S,
        "buzon": _S,
        "reportes_institucionales": _S,
        "bitacora_registro_acceso": _S,
    },
    "Docente con sección a cargo": {
        "usuarios_roles": _S,
        "datos_maestros": _S,
        "estudiantes_encargados": _V,
        "datos_sensibles": _S,
        "horarios_calendario": _E,
        "asistencia": _E,
        "notas": _E,
        "modificacion_notas": _S,
        "pagos_solvencia": _S,
        "documentos": _S,
        "avisos": _V,
        "reportes_conducta": _E,
        "buzon": _E,
        "reportes_institucionales": _S,
        "bitacora_registro_acceso": _S,
    },
    "Tallerista": {
        "usuarios_roles": _S,
        "datos_maestros": _S,
        "estudiantes_encargados": _V,
        "datos_sensibles": _S,
        "horarios_calendario": _E,
        "asistencia": _E,
        "notas": _S,
        "modificacion_notas": _S,
        "pagos_solvencia": _S,
        "documentos": _S,
        "avisos": _V,
        "reportes_conducta": _S,
        "buzon": _S,
        "reportes_institucionales": _S,
        "bitacora_registro_acceso": _S,
    },
    "Padre de familia": {
        "usuarios_roles": _S,
        "datos_maestros": _S,
        "estudiantes_encargados": _V,
        "datos_sensibles": _S,
        "horarios_calendario": _V,
        "asistencia": _V,
        "notas": _V,
        "modificacion_notas": _S,
        "pagos_solvencia": _V,
        "documentos": _V,
        "avisos": _V,
        "reportes_conducta": _V,
        "buzon": _E,
        "reportes_institucionales": _S,
        "bitacora_registro_acceso": _S,
    },
    "Administrador del sistema": {
        "usuarios_roles": _E,
        "datos_maestros": _E,
        "estudiantes_encargados": _V,
        "datos_sensibles": _V,
        "horarios_calendario": _V,
        "asistencia": _V,
        "notas": _V,
        "modificacion_notas": _S,
        "pagos_solvencia": _V,
        "documentos": _V,
        "avisos": _V,
        "reportes_conducta": _V,
        "buzon": _S,
        "reportes_institucionales": _V,
        "bitacora_registro_acceso": _V,
    },
}

_USERNAME_POR_ROL = {
    "Dirección": "dir.demo",
    "Coordinación": "coord.demo",
    "Encargado de pagos": "pagos.demo",
    "Docente": "docente.demo",
    "Docente con sección a cargo": "guia.demo",
    "Tallerista": "tallerista.demo",
    "Padre de familia": "familia.demo",
    "Administrador del sistema": "admin.demo",
}

# Contraseña de siembra ficticia, solo para desarrollo — nunca se usa en
# producción (regla de trabajo 10: ningún secreto real en el repositorio).
_CONTRASENA_SIEMBRA = "CambiaEstaClave2026"


class Command(BaseCommand):
    help = "Crea los 8 roles y un usuario de demostración por rol (Fase 3)."

    @transaction.atomic
    def handle(self, *args, **options):
        for nombre_rol, permisos in _MATRIZ.items():
            role, creado = Role.objects.update_or_create(
                name=nombre_rol, defaults={"permissions": permisos, "is_active": True}
            )
            self.stdout.write(("Creado" if creado else "Actualizado") + f" rol: {nombre_rol}")

            username = _USERNAME_POR_ROL[nombre_rol]
            if not User.objects.filter(username=username).exists():
                User.objects.create_user(
                    username=username,
                    password=_CONTRASENA_SIEMBRA,
                    role=role,
                    must_change_password=False,
                )
                self.stdout.write(f"  usuario de prueba: {username} / {_CONTRASENA_SIEMBRA}")

        self.stdout.write(self.style.SUCCESS("Semilla de la Fase 3 lista."))
