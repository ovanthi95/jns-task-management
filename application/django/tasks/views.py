"""Views for API 06 and API 07.

    API 06  POST /api/projects/:projectId/tasks   create a task in a project
    API 07  GET  /api/projects/:projectId/tasks   list that project's tasks

Tenant isolation
----------------
The Task model has no organisation_id column, so a task belongs to an
organisation through its project. Every request here loads the project with
`organisation_id` fixed to the caller's own organisation, which means a project
belonging to another organisation is simply not found.

That returns 404 rather than 403 on purpose. A 403 would confirm the project
exists, which tells an attacker something about a tenant they cannot see.
"""

from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from projects.models import Project

from .models import Task
from .serializers import TaskCreateSerializer, TaskSerializer


class ProjectTaskListCreateView(generics.ListCreateAPIView):
    """One view, two services: GET is API 07, POST is API 06."""

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return TaskCreateSerializer

        return TaskSerializer

    def get_project(self):
        """The project from the URL, or 404 if it is not this tenant's."""

        return get_object_or_404(
            Project,
            pk=self.kwargs["project_id"],
            organisation_id=self.request.user.organisation_id,
        )

    def get_queryset(self):
        """API 07."""

        project = self.get_project()

        return (
            Task.objects
            .filter(project=project)
            .select_related(
                "task_type",
                "status",
                "priority",
                "created_by",
            )
            .order_by("-created_at", "-task_id")
        )

    def create(self, request, *args, **kwargs):
        """API 06.

        The project comes from the URL and created_by from the token, so
        neither can be set by the request body.
        """

        project = self.get_project()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        task = serializer.save(
            project=project,
            created_by=request.user,
        )

        return Response(
            TaskSerializer(task).data,
            status=status.HTTP_201_CREATED,
        )
