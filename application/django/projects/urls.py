from django.urls import path

from projects.views import ProjectView


urlpatterns = [
    path("projects", ProjectView.as_view(), name="projects"),
]