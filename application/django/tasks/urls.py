"""Routes owned by the tasks app.

Only the two services on the agreed REST list are registered:

    API 06  POST /api/projects/:projectId/tasks
    API 07  GET  /api/projects/:projectId/tasks

The `api/` prefix is added once in config/urls.py, so it is not repeated here.

Note there is no trailing slash, because the agreed contract has none.
APPEND_SLASH is on by Django's default, but it only redirects when the slashed
form matches a registered route. Only the unslashed form is registered here, so
/api/projects/1/tasks/ is a plain 404 and a POST body can never be silently
dropped in a redirect. test_the_route_has_no_trailing_slash asserts this.
"""

from django.urls import path

from .views import ProjectTaskListCreateView
from tasks.api.file_upload import FileUploadView

urlpatterns = [
    path(
        "projects/<int:project_id>/tasks",
        ProjectTaskListCreateView.as_view(),
        name="project-tasks",
    ),
    path(
        "tasks/<int:task_id>/files",
        FileUploadView.as_view(),
        name="task-files",
    ),
]
