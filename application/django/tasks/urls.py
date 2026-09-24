"""Routes owned by the tasks app.

The task services registered here are:

    API 06  POST /api/projects/:projectId/tasks
    API 07  GET  /api/projects/:projectId/tasks
    API 10  POST /api/tasks/:taskId/files

The `api/` prefix is added once in config/urls.py, so it is not repeated here.

Note there is no trailing slash, because the agreed contract has none.
APPEND_SLASH is on by Django's default, but it only redirects when the slashed
form matches a registered route. Only the unslashed form is registered here, so
/api/projects/1/tasks/ is a plain 404 and a POST body can never be silently
dropped in a redirect. test_the_route_has_no_trailing_slash asserts this.

One path, two endpoint modules
------------------------------
The agreed contract puts APIs 06 and 07 on the same URL and separates them by
method, but the playbook's file map gives each service its own module. A URL
maps to exactly one view, so the two are joined here rather than by putting
both methods in one file.

ProjectTasksRoute therefore contributes no behaviour of its own. `get` comes
from API 07's view and `post` from API 06's view, and neither module knows the
other exists. permission_classes is restated rather than inherited so that the
list this route actually runs is visible in one place: IsAuthenticated covers
both methods, and CanCreateTask answers True for anything that is not a POST,
which leaves API 07 open to any member of the project.
"""

from django.urls import path
from rest_framework import permissions

from .api.file_upload import FileUploadView
from .api.task_create import CanCreateTask, TaskCreateView
from .api.task_list import TaskListView


class ProjectTasksRoute(TaskListView, TaskCreateView):
    """GET is API 07, POST is API 06."""

    permission_classes = [permissions.IsAuthenticated, CanCreateTask]


urlpatterns = [
    path(
        "projects/<int:project_id>/tasks",
        ProjectTasksRoute.as_view(),
        name="project-tasks",
    ),
    path(
        "tasks/<int:task_id>/files",
        FileUploadView.as_view(),
        name="task-files",
    ),
]
