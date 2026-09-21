"""
Crea la primera cuenta real de un entorno (típicamente el Administrador
del sistema) sin pasar la contraseña por la línea de comandos ni dejarla
en ningún archivo — la pide de forma interactiva, igual que
`createsuperuser`. `manage.py createsuperuser` no aplica en este proyecto
porque `accounts.User` no usa `is_staff`/`is_superuser`
(ver apps/accounts/models.py).
"""

import getpass

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from apps.accounts.models import Role, User


class Command(BaseCommand):
    help = "Crea el primer usuario de un entorno, con contraseña pedida de forma interactiva."

    def add_arguments(self, parser):
        parser.add_argument("--username", required=True)
        parser.add_argument(
            "--role",
            required=True,
            help="Nombre exacto del rol (por ejemplo, 'Administrador del sistema').",
        )
        parser.add_argument("--email", default="")

    def handle(self, *args, **options):
        username = options["username"]
        role_name = options["role"]
        email = options["email"]

        if User.objects.filter(username=username).exists():
            raise CommandError(f"Ya existe un usuario '{username}'.")

        try:
            role = Role.objects.get(name=role_name, is_active=True)
        except Role.DoesNotExist:
            raise CommandError(
                f"No existe el rol '{role_name}'. Corré antes la siembra de roles."
            ) from None

        password = getpass.getpass("Contraseña temporal: ")
        password_confirm = getpass.getpass("Confirmá la contraseña: ")
        if password != password_confirm:
            raise CommandError("Las contraseñas no coinciden.")

        try:
            validate_password(password)
        except ValidationError as exc:
            raise CommandError("\n".join(exc.messages)) from exc

        User.objects.create_user(
            username=username,
            password=password,
            role=role,
            email=email,
            must_change_password=True,
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Usuario '{username}' creado con el rol '{role_name}'. "
                "Deberá cambiar la contraseña en el primer ingreso."
            )
        )
