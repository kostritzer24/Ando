from django.urls import path

from . import views

urlpatterns = [
    path("reports/grades-summary/", views.GradesSummaryView.as_view(), name="report-grades-summary"),
    path("reports/attendance/", views.AttendanceReportView.as_view(), name="report-attendance"),
    path(
        "reports/insolvent-students/",
        views.InsolventStudentsView.as_view(),
        name="report-insolvent-students",
    ),
    path("reports/schedules/", views.SchedulesReportView.as_view(), name="report-schedules"),
    path(
        "reports/enrolled-students/", views.EnrolledStudentsView.as_view(), name="report-enrolled-students"
    ),
    path(
        "reports/grade-change-history/",
        views.GradeChangeHistoryView.as_view(),
        name="report-grade-change-history",
    ),
    path("reports/family-access/", views.FamilyAccessReportView.as_view(), name="report-family-access"),
    path(
        "reports/issued-documents/",
        views.IssuedDocumentsReportView.as_view(),
        name="report-issued-documents",
    ),
    path("reports/metrics/", views.MetricsView.as_view(), name="report-metrics"),
]
