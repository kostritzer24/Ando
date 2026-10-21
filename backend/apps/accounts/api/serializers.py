from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.accounts.models import Role, User


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["public_id", "name", "permissions", "is_active"]
        read_only_fields = ["public_id"]


class UserSerializer(serializers.ModelSerializer):
    role = serializers.SlugRelatedField(
        slug_field="public_id", queryset=Role.objects.filter(is_active=True)
    )
    role_name = serializers.CharField(source="role.name", read_only=True)

    class Meta:
        model = User
        fields = [
            "public_id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "role_name",
            "is_active",
            "must_change_password",
            "locked_until",
            "last_login",
        ]
        read_only_fields = [
            "public_id",
            "username",
            "role_name",
            "must_change_password",
            "locked_until",
            "last_login",
        ]


class MeSerializer(UserSerializer):
    """`/auth/me/`: la persona más los permisos de su rol por área
    (RNF-03), para que el frontend arme el menú y los botones desde la
    misma matriz que aplica el backend, en vez de repetir nombres de rol."""

    permissions = serializers.JSONField(source="role.permissions", read_only=True)

    class Meta(UserSerializer.Meta):
        fields = [*UserSerializer.Meta.fields, "permissions"]


class UserCreateSerializer(serializers.Serializer):
    """RF-01: crear usuario y asignarle un rol, con contraseña temporal."""

    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    first_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    role = serializers.SlugRelatedField(
        slug_field="public_id", queryset=Role.objects.filter(is_active=True)
    )
    contrasena_temporal = serializers.CharField(write_only=True)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Ya existe un usuario con ese nombre de usuario.")
        return value

    def validate_contrasena_temporal(self, value):
        validate_password(value)
        return value


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)


class ChangePasswordSerializer(serializers.Serializer):
    # En el cambio obligatorio del primer ingreso la sesión ya se probó con
    # la contraseña temporal al entrar: pedirla otra vez solo agrega un
    # campo más que equivocar. En el cambio voluntario sí es obligatoria.
    contrasena_actual = serializers.CharField(
        write_only=True, trim_whitespace=False, required=False, allow_blank=True
    )
    contrasena_nueva = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_contrasena_nueva(self, value):
        validate_password(value, user=self.context.get("user"))
        return value

    def validate(self, attrs):
        user = self.context["user"]
        actual = attrs.get("contrasena_actual", "")
        if not user.must_change_password and not actual:
            raise serializers.ValidationError(
                {"contrasena_actual": "Escribe tu contraseña actual."}
            )
        if actual == attrs["contrasena_nueva"] or user.check_password(attrs["contrasena_nueva"]):
            raise serializers.ValidationError(
                {"contrasena_nueva": "La contraseña nueva debe ser distinta de la actual."}
            )
        return attrs


class ResetPasswordSerializer(serializers.Serializer):
    contrasena_temporal = serializers.CharField(write_only=True)

    def validate_contrasena_temporal(self, value):
        validate_password(value)
        return value
