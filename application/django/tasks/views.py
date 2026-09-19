"""Views for API 06 and API 07.

    API 06  POST /api/projects/:projectId/tasks   create and assign a task
    API 07  GET  /api/projects/:projectId/tasks   list that project's tasks

Who can reach a project
-----------------------
The Task model has no organisation_id column, so a task belongs to an
organisation through its project. Both services load the project with two
conditions fixed: it is in the caller's own organisation, and the caller holds
a ProjectMember row for it.

Membership is explicit. Project.created_by is not treated as implicit
membership here, because writing that row belongs to the project-creation
service (API 04), not to this one.

A project failing either condition returns 404 rather than 403, so a project in
another organisation, a project the caller is not a member of, and a project id
that does not exist are indistinguishable. A 403 would confirm the project
exists, which tells an attacker something about a tenant they cannot see.

Who can create
--------------
API 06 is further restricted to the Admin and Manager roles. That is a property
of the caller alone rather than of any project, so it is answered with 403 and
leaks nothing. API 07 stays open to any member of the project.
"""

from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from projects.models import Project

from .models import Task
from .serializers import TaskCreateSerializer, TaskSerializer

# Matched case-insensitively against Role.role_name, whose seeded values are
# Admin, Manager, Employee, Intern and Volunteer
# (users/management/commands/seed_lookups.py).
TASK_CREATOR_ROLES = frozenset({"admin", "manager"})


class CanCreateTask(permissions.BasePermission):
    """The role restriction on API 06. API 07 is not affected."""

    message = "Your role is not permitted to create tasks."

    def has_permission(self, request, view):
        if request.method != "POST":
            return True

        role = getattr(request.user, "role", None)

        return (
            role is not None
            and role.role_name.lower() in TASK_CREATOR_ROLES
        )


class ProjectTaskListCreateView(generics.ListCreateAPIView):
    """One view, two services: GET is API 07, POST is API 06."""

    permission_classes = [permissions.IsAuthenticated, CanCreateTask]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return TaskCreateSerializer

        return TaskSerializer

    def get_project(self):
        """The project from the URL, or 404 if this caller cannot reach it.

        Organisation and membership are both pushed into the query rather than
        checked afterwards, so there is no branch that could answer one of them
        with a different status code.

        Cached because a POST asks for the project twice: once to build the
        serializer context and once to save.
        """

        if not hasattr(self, "_project"):
            self._project = get_object_or_404(
                Project.objects.filter(members__user=self.request.user),
                pk=self.kwargs["project_id"],
                organisation_id=self.request.user.organisation_id,
            )

        return self._project

    def get_serializer_context(self):
        """API 06 validates the assignee against the project, so pass it in."""

        context = super().get_serializer_context()

        if self.request.method == "POST":
            context["project"] = self.get_project()

        return context

    def _filter_id(self, name):
        """A query parameter as an int, or 400 if it is not a number.

        Without this, ?status_id=abc reaches the ORM, which raises ValueError
        and surfaces as a 500 instead of a bad request. All three supported
        filters go through here, so all three answer a malformed value the
        same way.

        An id that is a valid integer but matches no row is not an error. It
        simply selects nothing, and the caller gets an empty list.
        """

        raw = self.request.query_params.get(name)

        if raw is None:
            return None

        try:
            return int(raw)
        except (TypeError, ValueError):
            raise ValidationError({name: "Must be an integer."})

    def get_queryset(self):
        """API 07.

        Three filters are supported: status_id, priority_id and assignee_id.
        Supplying more than one narrows the result, because each is applied to
        the queryset the previous one returned.

        Ordering is fixed rather than client-controlled, so a page of results
        is reproducible: newest first, with the task id breaking ties between
        rows created in the same instant.

        select_related follows the four forward keys inside the same query.
        assignees needs prefetch_related instead, because it is a reverse many
        relation: without it, serializing the array would cost two more
        queries for every task returned.
        """

        queryset = (
            Task.objects
            .filter(project=self.get_project())
            .select_related(
                "task_type",
                "status",
                "priority",
                "created_by",
            )
            .prefetch_related("assignees__user")
        )

        status_id = self._filter_id("status_id")

        if status_id is not None:
            queryset = queryset.filter(status_id=status_id)

        priority_id = self._filter_id("priority_id")

        if priority_id is not None:
            queryset = queryset.filter(priority_id=priority_id)

        assignee_id = self._filter_id("assignee_id")

        if assignee_id is not None:
            # This one joins through task_assignees, which can repeat a task
            # row. (task, user) is unique today so a single id cannot, but the
            # collapse keeps that true if the filter ever takes a list.
            queryset = (
                queryset
                .filter(assignees__user_id=assignee_id)
                .distinct()
            )

        return queryset.order_by("-created_at", "-task_id")

    def create(self, request, *args, **kwargs):
        """API 06.

        The project comes from the URL and created_by from the token, so
        neither can be set by the request body. The serializer writes the task
        and its assignment together in one transaction.
        """

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        task = serializer.save(
            project=self.get_project(),
            created_by=request.user,
        )

        return Response(
            TaskSerializer(task).data,
            status=status.HTTP_201_CREATED,
        )
