from django.urls import path

from projects.api.project_members import ProjectMembersView
from projects.api.project_update import ProjectUpdateView
from projects.views import ProjectView


urlpatterns = [
    path("projects", ProjectView.as_view(), name="projects"),
    path(
        "projects/<int:project_id>/members",
        ProjectMembersView.as_view(),
        name="project-members",
    ),
    path(
        "projects/<int:project_id>",
        ProjectUpdateView.as_view(),
        name="project-update",
    ),
]
