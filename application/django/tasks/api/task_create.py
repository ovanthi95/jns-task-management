"""API 06 - POST /api/projects/:projectId/tasks.

The existing task-creation service remains authoritative for project access,
lookup validation, assignment rules and the stored-procedure write. This HTTP
layer adds only the optional post-create email notification.
"""

from rest_framework import status
from rest_framework.permissions import AllowAny
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

from ._session import not_authenticated, session_user

ROLE_NOT_PERMITTED = "Your role is not permitted to create tasks."


class TaskCreateView(APIView):
    """API 06.

    authentication_classes is emptied and the caller is read out of the
    session instead, which is the convention APIs 02, 03, 04, 05 and 10
    already follow. tasks/api/_session.py explains why request.user cannot be
    used here.

    The route-level CanCreateTask permission class this view used to carry is
    gone with it: a DRF permission class is handed request.user, which is
    always AnonymousUser under session auth, so it could never have answered
    the question. The same rule is applied inside post() against the session
    user instead.
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request, project_id):
        user = session_user(request)

        if user is None:
            return not_authenticated()

        # The role is answered before the body is parsed, so a caller whose
        # role is not permitted is told that rather than being told its body
        # was malformed, which would be a hint about a service it cannot use.
        if not task_create_service.user_may_create_task(user):
            return Response(
                {"detail": ROLE_NOT_PERMITTED},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = TaskCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = dict(serializer.validated_data)
        notify_assignee = bool(data.pop("notify_assignee", False))

        # `user` is already the session dict sp_get_session_user returned,
        # so the notification permission is answered straight off it. The
        # previous request.user.user_id lookup could not work here.
        if notify_assignee and not actor_has_permission(
            user, "send_task_notifications"
        ):
            return Response(
                {"detail": "Task notification permission required."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            task = task_create_service.create_task(
                project_id=project_id,
                user=user,
                data=data,
            )
        except ProjectNotVisible:
            return Response(
                {"detail": "Not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except RoleNotPermitted as error:
            # The role gate above has already answered this for requests that
            # come in over HTTP. Mapped here as well so the endpoint still
            # behaves if the rule is ever tightened inside the service alone.
            return Response(
                {"detail": error.message},
                status=status.HTTP_403_FORBIDDEN,
            )
        except InvalidTaskInput as error:
            return Response(
                error.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_data = dict(TaskSerializer(task).data)
        response_data["email_requested"] = notify_assignee
        response_data["email_sent"] = False

        if notify_assignee:
            try:
                response_data["email_sent"] = send_task_assignment_email(
                    task_id=task["task_id"],
                    assigned_by_name=(
                        f'{user["first_name"]} {user["last_name"]}'
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
