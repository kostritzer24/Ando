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
        ]
        read_only_fields = ["public_id", "role_name", "must_change_password"]


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
    contrasena_actual = serializers.CharField(write_only=True, trim_whitespace=False)
    contrasena_nueva = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_contrasena_nueva(self, value):
        validate_password(value, user=self.context.get("user"))
        return value


class ResetPasswordSerializer(serializers.Serializer):
    contrasena_temporal = serializers.CharField(write_only=True)

    def validate_contrasena_temporal(self, value):
        validate_password(value)
        return value
