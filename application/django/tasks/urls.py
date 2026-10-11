"""Task API routes."""

from django.urls import path
from rest_framework import permissions

from .api.comment_create import TaskCommentView
from .api.file_upload import FileDownloadView, FileUploadView
from .api.task_create import CanCreateTask, TaskCreateView
from .api.task_list import TaskListView
from .api.task_options import ProjectTaskOptionsView
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
    path(
        "tasks/<int:task_id>/files/<int:attachment_id>/download",
        FileDownloadView.as_view(),
        name="task-file-download",
    ),
]
