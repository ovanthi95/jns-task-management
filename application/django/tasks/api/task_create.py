"""API 06 - POST /api/projects/:projectId/tasks

Code owner: Edward

This module is the HTTP layer and nothing else. Its whole job is:

    parse the body -> check types -> call one service -> map the failure to a
    status code -> render the result.

Every rule about who may create a task, which ids have to exist and what gets
written lives in tasks/services/task_create_service.py. Nothing here touches
the database, the ORM or a stored procedure.

Two values are deliberately not read from the request body:

    project_id  comes from the URL
    created_by  comes from the session

so a forged body cannot put a task in another organisation's project or
attribute it to someone else.

Status codes this endpoint can answer with:

    201  created, body is the task in API 07's read shape
    400  the body failed parsing, or a business rule rejected it
    401  no session
    403  authenticated, but this role may not create tasks
    404  the project does not exist, or this caller may not see that it does
"""

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..serializers import TaskCreateSerializer, TaskSerializer
from ..services import task_create_service
from ..services.exceptions import (
    InvalidTaskInput,
    ProjectNotVisible,
    RoleNotPermitted,
)


class CanCreateTask(permissions.BasePermission):
    """The role rule, asked before the body is parsed.

    The rule itself is not defined here. It is read from the service, so there
    is one definition of who may create a task and this class cannot drift
    away from it.

    Running it as a DRF permission rather than letting the service raise
    RoleNotPermitted is what keeps 403 ahead of 400: a caller whose role is
    not permitted is told that, rather than being told its request body was
    malformed, which would be a hint about a service it cannot use anyway.

    Returns True for anything that is not a POST, because API 07 shares this
    route and is open to any member of the project.
    """

    message = "Your role is not permitted to create tasks."

    def has_permission(self, request, view):
        if request.method != "POST":
            return True

        return task_create_service.user_may_create_task(request.user)


class TaskCreateView(APIView):
    """API 06."""

    permission_classes = [permissions.IsAuthenticated, CanCreateTask]

    def post(self, request, project_id):
        serializer = TaskCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            task = task_create_service.create_task(
                project_id=project_id,
                user=request.user,
                data=serializer.validated_data,
            )
        except ProjectNotVisible:
            return Response(
                {"detail": "Not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except RoleNotPermitted as error:
            # CanCreateTask has already answered this for requests that come
            # in over HTTP. Mapped here as well so the endpoint still behaves
            # if the rule is ever tightened inside the service alone.
            return Response(
                {"detail": error.message},
                status=status.HTTP_403_FORBIDDEN,
            )
        except InvalidTaskInput as error:
            # Same shape as the serializer's own errors: keyed by the field
            # name the client sent, with a list of messages.
            return Response(error.errors, status=status.HTTP_400_BAD_REQUEST)

        # Rendered through the read serializer rather than returned raw, so
        # the decimals stay strings ("4.50") and the timestamps stay
        # "...Z". A raw Decimal through Response would come out as a float
        # and break the agreed contract.
        return Response(
            TaskSerializer(task).data,
            status=status.HTTP_201_CREATED,
        )
