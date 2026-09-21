import uuid

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models
from django.utils import timezone

#: Las 15 áreas de permiso de docs/permisos-roles.md. Vive aquí (no solo en
#: la documentación) porque tanto el seed de roles como las pruebas de
#: acceso no autorizado necesitan la lista exacta.
AREAS_PERMISO = [
    "usuarios_roles",
    "datos_maestros",
    "estudiantes_encargados",
    "datos_sensibles",
    "horarios_calendario",
    "asistencia",
    "notas",
    "modificacion_notas",
    "pagos_solvencia",
    "documentos",
    "avisos",
    "reportes_conducta",
    "buzon",
    "reportes_institucionales",
    "bitacora_registro_acceso",
]

NIVELES_PERMISO = ["ver", "editar", "sin_acceso"]


class Role(models.Model):
    """Rol (RNF-03): Dirección, Coordinación, Encargado de pagos, Docente,
    Docente con sección a cargo, Tallerista, Padre de familia,
    Administrador del sistema — ver docs/permisos-roles.md."""

    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField("nombre", max_length=60, unique=True)
    permissions = models.JSONField(
        "permisos",
        default=dict,
        help_text="Mapa de área (AREAS_PERMISO) → nivel (NIVELES_PERMISO).",
    )
    is_active = models.BooleanField("activo", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "rol"
        verbose_name_plural = "roles"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def nivel_en(self, area: str) -> str:
        return self.permissions.get(area, "sin_acceso")


class UserManager(BaseUserManager):
    def create_user(self, username: str, password: str | None = None, **extra_fields):
        if not username:
            raise ValueError("El usuario necesita un nombre de usuario.")
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    """Usuario (RN-14: código interno único para estudiantes, pero las
    cuentas de acceso las crea únicamente la administración — sin
    registro libre, sección 14.1).

    No hereda de PermissionsMixin ni instala django.contrib.admin: el
    control de acceso es la matriz de `Role.permissions`, no el sistema
    de permisos de Django. Por eso tampoco define `is_staff`/
    `is_superuser` — `manage.py createsuperuser` no aplica aquí, se usa
    `manage.py create_initial_user` en su lugar.
    """

    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    username = models.CharField("nombre de usuario", max_length=150, unique=True)
    email = models.EmailField("correo electrónico", blank=True)
    first_name = models.CharField("nombres", max_length=100, blank=True)
    last_name = models.CharField("apellidos", max_length=100, blank=True)
    role = models.ForeignKey(
        Role, verbose_name="rol", on_delete=models.PROTECT, related_name="users"
    )
    is_active = models.BooleanField("activo", default=True)
    must_change_password = models.BooleanField("debe cambiar la contraseña", default=True)
    failed_login_attempts = models.PositiveIntegerField("intentos fallidos", default=0)
    locked_until = models.DateTimeField("bloqueado hasta", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"
        ordering = ["username"]

    def __str__(self) -> str:
        return self.username

    @property
    def esta_bloqueado(self) -> bool:
        return bool(self.locked_until and self.locked_until > timezone.now())

    def nombre_completo(self) -> str:
        return f"{self.first_name} {self.last_name}".strip() or self.username
