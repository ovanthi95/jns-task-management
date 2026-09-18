"""Routes owned by the tasks app.

Only the two services on the agreed REST list are registered:

    API 06  POST /api/projects/:projectId/tasks
    API 07  GET  /api/projects/:projectId/tasks

The `api/` prefix is added once in config/urls.py, so it is not repeated here.

Note there is no trailing slash, because the agreed contract has none. Django
appends one by default on a 404, so /api/projects/1/tasks/ will redirect rather
than fail, but the canonical form is the one written below.
"""

from django.urls import path

from .views import ProjectTaskListCreateView

urlpatterns = [
    path(
        "projects/<int:project_id>/tasks",
        ProjectTaskListCreateView.as_view(),
        name="project-tasks",
    ),
]
