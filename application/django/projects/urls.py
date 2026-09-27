from django.urls import path

from projects.api.project_update import ProjectUpdateView
from projects.views import ProjectView


urlpatterns = [
    path("projects", ProjectView.as_view(), name="projects"),
    path(
        "projects/<int:project_id>",
        ProjectUpdateView.as_view(),
        name="project-update",
    ),
]
