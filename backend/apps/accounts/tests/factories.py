import factory
from factory.django import DjangoModelFactory

from apps.accounts.models import Role, User


class RoleFactory(DjangoModelFactory):
    class Meta:
        model = Role

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
