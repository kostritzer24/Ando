from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("api/v1/", include("apps.accounts.api.urls")),
    path("api/v1/", include("apps.core.api.urls")),
    path("api/v1/", include("apps.catalog.api.urls")),
    path("api/v1/", include("apps.students.api.urls")),
    path("api/v1/", include("apps.scheduling.api.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/schema/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="schema-docs"),
]
