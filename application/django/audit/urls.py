from django.urls import path

from audit.api.task_audit import TaskAuditView


urlpatterns = [
    path(
        "tasks/<int:task_id>/audit",
        TaskAuditView.as_view(),
        name="task-audit",
    ),
]
