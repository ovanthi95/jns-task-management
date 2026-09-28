from django.urls import path

from projects.views import ProjectView
from projects.api.project_update import ProjectUpdateView


urlpatterns = [
    path("projects", ProjectView.as_view(), name="projects"),
    path("projects/<int:project_id>", ProjectUpdateView.as_view(), name="project-update"),
]