from django.urls import path

from .api.file_upload import FileUploadView
from .api.task_create import TaskCreateView
from .api.task_list import TaskListView
from .api.task_options import TaskCreateOptionsView


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
        TaskCreateOptionsView.as_view(),
        name="project-task-options",
    ),
    path(
        "tasks/<int:task_id>/files",
        FileUploadView.as_view(),
        name="task-files",
    ),
]
