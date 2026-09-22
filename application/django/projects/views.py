from django.db.models import Q
from rest_framework import generics, permissions, status
from rest_framework.response import Response

from .models import Project
from .serializers import ProjectCreateSerializer, ProjectSerializer


PROJECT_CREATOR_ROLES = frozenset({"admin", "manager"})


class CanCreateProject(permissions.BasePermission):
    """Only Admin and Manager can create projects."""

    message = "Your role is not permitted to create projects."

    def has_permission(self, request, view):
        if request.method != "POST":
            return True

        role = getattr(request.user, "role", None)

        return (
            role is not None
            and role.role_name.lower() in PROJECT_CREATOR_ROLES
        )


class ProjectListCreateView(generics.ListCreateAPIView):
    """API 04 POST /api/projects and API 05 GET /api/projects."""

    permission_classes = [
        permissions.IsAuthenticated,
        CanCreateProject,
    ]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ProjectCreateSerializer

        return ProjectSerializer

    def get_queryset(self):
        """Return projects visible to the authenticated user."""

        user = self.request.user
        role_name = user.role.role_name.lower()

        queryset = Project.objects.filter(
            organisation_id=user.organisation_id
        )

        # Admin can see every project in their organisation.
        if role_name == "admin":
            return queryset.order_by("-created_at", "-project_id")

        # Manager can see projects they created or belong to.
        if role_name == "manager":
            queryset = queryset.filter(
                Q(created_by=user) | Q(members__user=user)
            ).distinct()

            return queryset.order_by("-created_at", "-project_id")

        # Employee, Intern and Volunteer can see projects
        # where they are explicit members.
        queryset = queryset.filter(
            members__user=user
        ).distinct()

        return queryset.order_by("-created_at", "-project_id")

    def create(self, request, *args, **kwargs):
        """Create a project and return the normal project read shape."""

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        project = serializer.save()

        return Response(
            ProjectSerializer(project).data,
            status=status.HTTP_201_CREATED,
        )
