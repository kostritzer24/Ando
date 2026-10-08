from django.conf import settings
from django.utils import timezone
from django.utils.dateformat import format as formatear_fecha
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.domain.gestion_usuarios import CambioNoPermitido
from apps.accounts.models import Role, User
from apps.accounts.services import (
    CredencialesInvalidas,
    UsuarioBloqueado,
    actualizar_usuario,
    cambiar_contrasena,
    crear_usuario,
    iniciar_sesion,
    restablecer_contrasena,
)
from apps.core.api.mixins import RegistraAccesoMixin
from apps.core.permissions import PermisoPorArea

from .serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    MeSerializer,
    ResetPasswordSerializer,
    RoleSerializer,
    UserCreateSerializer,
    UserSerializer,
)

_REFRESH_LIFETIME_SECONDS = int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds())
_AUTH_COOKIE_PATH = "/api/v1/auth/"


def _set_refresh_cookie(response: Response, refresh_token_str: str) -> None:
    response.set_cookie(
        settings.REFRESH_COOKIE_NAME,
        refresh_token_str,
        max_age=_REFRESH_LIFETIME_SECONDS,
        httponly=True,
        secure=settings.REFRESH_COOKIE_SECURE,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
        path=_AUTH_COOKIE_PATH,
    )


def _delete_refresh_cookie(response: Response) -> None:
    response.delete_cookie(settings.REFRESH_COOKIE_NAME, path=_AUTH_COOKIE_PATH)


# "30 de septiembre": en el formato de Django, la barra escapa letras que
# si no serían códigos de fecha ("d" es el día, "e" la zona horaria).
FORMATO_DIA = r"j \d\e F"


def _cuando(momento) -> str:
    """Hora local de Guatemala, no UTC (el datetime llega en UTC con
    USE_TZ). El bloqueo por RN-16 dura 24 horas: si no es hoy, se dice el
    día — "después de las 11:24" sin fecha hacía pensar que era hoy."""
    local = timezone.localtime(momento)
    if local.date() == timezone.localdate():
        return f"las {local:%H:%M}"
    return f"las {local:%H:%M} del {formatear_fecha(local, FORMATO_DIA)}"


class LoginView(APIView):
    """POST /auth/login/ — RF-27. Devuelve el token de acceso en el cuerpo
    y deja el token de refresco en una cookie HttpOnly/Secure/SameSite=Strict
    (sección 14.1)."""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    @extend_schema(request=LoginSerializer, responses=MeSerializer)
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user, refresh = iniciar_sesion(**serializer.validated_data)
        except CredencialesInvalidas:
            raise AuthenticationFailed("Usuario o contraseña incorrectos.") from None
        except UsuarioBloqueado as exc:
            raise AuthenticationFailed(
                "Esta cuenta está bloqueada temporalmente. "
                f"Puedes volver a intentarlo después de {_cuando(exc.bloqueado_hasta)}."
            ) from exc

        response = Response({"access": str(refresh.access_token), "user": MeSerializer(user).data})
        _set_refresh_cookie(response, str(refresh))
        return response


class RefreshView(APIView):
    """POST /auth/refresh/ — rota el token de acceso a partir de la cookie
    de refresco. Con ROTATE_REFRESH_TOKENS + BLACKLIST_AFTER_ROTATION
    (config/settings/base.py), simplejwt ya emite y revoca el token viejo."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=None,
        responses={200: {"type": "object", "properties": {"access": {"type": "string"}}}},
    )
    def post(self, request):
        token_str = request.COOKIES.get(settings.REFRESH_COOKIE_NAME)
        if not token_str:
            raise AuthenticationFailed("No hay sesión activa.")

        serializer = TokenRefreshSerializer(data={"refresh": token_str})
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as exc:
            raise AuthenticationFailed("La sesión expiró. Inicia sesión de nuevo.") from exc

        data = serializer.validated_data
        response = Response({"access": data["access"]})
        _set_refresh_cookie(response, data.get("refresh", token_str))
        return response


class LogoutView(APIView):
    """POST /auth/logout/ — revoca el token de refresco actual."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(request=None, responses=None)
    def post(self, request):
        token_str = request.COOKIES.get(settings.REFRESH_COOKIE_NAME)
        if token_str:
            try:
                RefreshToken(token_str).blacklist()
            except TokenError:
                pass
        response = Response(status=status.HTTP_204_NO_CONTENT)
        _delete_refresh_cookie(response)
        return response


class ChangePasswordView(APIView):
    """POST /auth/change-password/ — cambio obligatorio de la contraseña
    temporal en el primer ingreso (sección 14.1)."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=ChangePasswordSerializer, responses=None)
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"user": request.user})
        serializer.is_valid(raise_exception=True)
        if not request.user.check_password(serializer.validated_data["contrasena_actual"]):
            raise AuthenticationFailed("La contraseña actual no es correcta.")
        cambiar_contrasena(
            user=request.user,
            contrasena_nueva=serializer.validated_data["contrasena_nueva"],
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(RegistraAccesoMixin, APIView):
    """GET /auth/me/ — quién soy. Separado de `/users/{id}/` (área
    "Usuarios y roles", exclusiva de Dirección/Administrador) a propósito:
    cualquier persona autenticada puede consultar su propio perfil, no
    hace falta un permiso de administración para eso. Es lo que el
    frontend usa para reconstruir la sesión después de recargar la
    página — el token de acceso vive solo en memoria (sección 14.1), así
    que un refresco de navegador lo pierde y hay que reconstruir el
    usuario a partir de la cookie de refresco."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses=MeSerializer)
    def get(self, request):
        return Response(MeSerializer(request.user).data)


class UserViewSet(RegistraAccesoMixin, viewsets.ModelViewSet):
    """RF-01: crear usuarios y asignarles un rol. Solo Dirección y
    Administrador (docs/permisos-roles.md)."""

    queryset = User.objects.select_related("role").order_by("username")
    serializer_class = UserSerializer
    permission_classes = [PermisoPorArea]
    area = "usuarios_roles"
    lookup_field = "public_id"
    # Sin DELETE ni PUT: una cuenta nunca se borra (queda en la bitácora de
    # todo lo que hizo), se desactiva con PATCH `is_active`. Antes el
    # ModelViewSet completo dejaba borrarla de verdad.
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        return UserSerializer

    def create(self, request, *args, **kwargs):
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = dict(serializer.validated_data)
        contrasena_temporal = datos.pop("contrasena_temporal")
        user = crear_usuario(
            creado_por=request.user,
            contrasena_temporal=contrasena_temporal,
            **datos,
        )
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = UserSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            user = actualizar_usuario(
                actualizado_por=request.user, user=user, **serializer.validated_data
            )
        except CambioNoPermitido as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        return Response(UserSerializer(user).data)

    @action(detail=True, methods=["post"], url_path="reset-password")
    def reset_password(self, request, public_id=None):
        """POST /users/{public_id}/reset-password/ — restablecimiento
        gestionado por administración, nunca por correo automático."""
        user = self.get_object()
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        restablecer_contrasena(
            restablecido_por=request.user,
            user=user,
            contrasena_temporal=serializer.validated_data["contrasena_temporal"],
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class RoleViewSet(RegistraAccesoMixin, viewsets.ReadOnlyModelViewSet):
    """GET /roles/ — RNF-03. Solo Dirección y Administrador. De solo
    lectura: los permisos de cada rol son la matriz de
    docs/permisos-roles.md, sembrada por `seed_fase3`; cambiarlos desde la
    API (o borrar un rol con usuarios) la dejaría desalineada en silencio."""

    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [PermisoPorArea]
    area = "usuarios_roles"
    lookup_field = "public_id"
