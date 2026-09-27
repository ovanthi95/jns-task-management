from django.urls import path

from audit.api.history import HistoryView
from audit.api.task_audit import TaskAuditView


urlpatterns = [
    path("history", HistoryView.as_view(), name="history"),
    path(
        "tasks/<int:task_id>/audit",
        TaskAuditView.as_view(),
        name="task-audit",
    ),
]
