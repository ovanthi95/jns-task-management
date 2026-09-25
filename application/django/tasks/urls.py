"""Routes owned by the tasks app.

Registered task services:
    API 06  POST  /api/projects/:projectId/tasks
    API 07  GET   /api/projects/:projectId/tasks
    API 08  PATCH /api/tasks/:taskId
    API 09  POST  /api/tasks/:taskId/comments
    API 10  POST  /api/tasks/:taskId/files

The api/ prefix is added once in config/urls.py.
"""

from django.urls import path
from rest_framework import permissions

from .api.comment_create import TaskCommentView
from .api.file_upload import FileUploadView
from .api.task_create import CanCreateTask, TaskCreateView
from .api.task_list import TaskListView
from .api.task_update import TaskUpdateView


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
