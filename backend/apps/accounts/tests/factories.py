import factory
from factory.django import DjangoModelFactory

from apps.accounts.models import Role, User


class RoleFactory(DjangoModelFactory):
    class Meta:
        model = Role
        # Si dos llamadas en la misma prueba piden el mismo nombre (por
        # ejemplo, dos docentes distintos con rol "Docente"), reutiliza la
        # fila en vez de chocar con el `unique=True` de Role.name — así
        # es en producción: el rol es uno solo, lo que varía es el usuario.
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"Rol de prueba {n}")
    permissions = factory.LazyFunction(dict)
    is_active = True


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    username = factory.Sequence(lambda n: f"usuario{n}")
    role = factory.SubFactory(RoleFactory)
    must_change_password = False

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        self.set_password(extracted or "Prueba-Segura-2026")
        if create:
            self.save()
