"""API 06 - POST /api/projects/:projectId/tasks."""

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
from ._session import not_authenticated, session_user


class TaskCreateView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request, project_id):
        user = session_user(request)

        if user is None:
            return not_authenticated()

        if not task_create_service.user_may_create_task(user):
            return Response(
                {"detail": "Your role is not permitted to create tasks."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = TaskCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            task = task_create_service.create_task(
                project_id=project_id,
                user=user,
                data=serializer.validated_data,
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

        return Response(
            TaskSerializer(task).data,
            status=status.HTTP_201_CREATED,
        )
