"""Routes owned by the tasks app.

The task services registered here are:

    API 06  POST /api/projects/:projectId/tasks
    API 07  GET  /api/projects/:projectId/tasks
    API 08  PATCH /api/tasks/:taskId
    API 10  POST /api/tasks/:taskId/files
    Supporting  GET /api/projects/:projectId/task-options
    Supporting  POST /api/tasks/:taskId/comments

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
other exists. Each method now reads the caller out of the session itself, so
there is no route-level permission list that has to be kept in step with the
two modules: API 07 stays open to any member of the project, and the role gate
on task creation lives inside API 06's own post().
"""

from django.urls import path

from .api.comment_create import TaskCommentView
from .api.file_upload import FileUploadView
from .api.task_create import TaskCreateView
from .api.task_list import TaskListView
from .api.task_options import ProjectTaskOptionsView
from .api.task_update import TaskUpdateView


class ProjectTasksRoute(TaskListView, TaskCreateView):
    """GET is API 07, POST is API 06."""


urlpatterns = [
    path(
        "projects/<int:project_id>/tasks",
        ProjectTasksRoute.as_view(),
        name="project-tasks",
    ),
    path(
        "projects/<int:project_id>/task-options",
        ProjectTaskOptionsView.as_view(),
        name="project-task-options",
    ),
    path(
        "tasks/<int:task_id>",
        TaskUpdateView.as_view(),
        name="task-update",
    ),
    path(
        "tasks/<int:task_id>/comments",
        TaskCommentView.as_view(),
        name="task-comments",
    ),
    path(
        "tasks/<int:task_id>/files",
        FileUploadView.as_view(),
        name="task-files",
    ),
]
