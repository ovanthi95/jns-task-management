"""API 06 - POST /api/projects/:projectId/tasks.

The existing task-creation service remains authoritative for project access,
lookup validation, assignment rules and the stored-procedure write. This HTTP
layer adds only the optional post-create email notification.
"""

from django.db import DatabaseError
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
from ..services.task_notification_service import send_task_assignment_email
from users.services.permission_service import actor_has_permission
from users.services.session_service import get_authenticated_session_user


class CanCreateTask(permissions.BasePermission):
    message = "Your role is not permitted to create tasks."

    def has_permission(self, request, view):
        if request.method != "POST":
            return True
        return task_create_service.user_may_create_task(request.user)


class TaskCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated, CanCreateTask]

    def post(self, request, project_id):
        serializer = TaskCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = dict(serializer.validated_data)
        notify_assignee = bool(data.pop("notify_assignee", False))

        actor = get_authenticated_session_user(request.user.user_id)

        if notify_assignee and (
            actor is None
            or not actor_has_permission(actor, "send_task_notifications")
        ):
            return Response(
                {"detail": "Task notification permission required."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            task = task_create_service.create_task(
                project_id=project_id,
                user=request.user,
                data=data,
            )
        except ProjectNotVisible:
            return Response(
                {"detail": "Not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except RoleNotPermitted as error:
            return Response(
                {"detail": error.message},
                status=status.HTTP_403_FORBIDDEN,
            )
        except InvalidTaskInput as error:
            return Response(
                error.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )
        except DatabaseError as error:
            if "other task type is required" in str(error).lower():
                return Response(
                    {"other_task_type": ["Please specify the task type when Other is selected."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            raise

        response_data = dict(TaskSerializer(task).data)
        response_data["email_requested"] = notify_assignee
        response_data["email_sent"] = False

        if notify_assignee:
            try:
                response_data["email_sent"] = send_task_assignment_email(
                    task_id=task["task_id"],
                    assigned_by_name=(
                        f"{request.user.first_name} {request.user.last_name}"
                    ).strip(),
                )
                if not response_data["email_sent"]:
                    response_data["email_warning"] = (
                        "The task was created, but no assignment email was sent."
                    )
            except Exception:
                response_data["email_warning"] = (
                    "The task was created, but the assignment email could not be sent."
                )

        return Response(
            response_data,
            status=status.HTTP_201_CREATED,
        )
