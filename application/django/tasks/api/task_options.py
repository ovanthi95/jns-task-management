"""Support endpoint for API 06 create-task form options."""

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from data_access.tasks.get_task_create_options import get_task_create_options
from tasks.services import task_create_service
from tasks.services.exceptions import ProjectNotVisible
from tasks.services.project_access import require_visible_project

from ._session import not_authenticated, session_user


class TaskCreateOptionsView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, project_id):
        user = session_user(request)

        if user is None:
            return not_authenticated()

        try:
            project = require_visible_project(project_id=project_id, user=user)
        except ProjectNotVisible:
            return Response(
                {"detail": "Not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        options = get_task_create_options(project_id)

        return Response({
            **options,
            "can_create": (
                task_create_service.user_may_create_task(user)
                and (project.get("project_status") or "").lower() == "active"
            ),
        })
