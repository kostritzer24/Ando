from django.urls import path

from . import views

urlpatterns = [
    path("audit-log/", views.AuditLogListView.as_view(), name="audit-log-list"),
    path("access-log/", views.AccessLogListView.as_view(), name="access-log-list"),
]
