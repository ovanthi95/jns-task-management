# API 07 - Task list
# Owner: Edward

"""API 07 - GET /api/projects/:projectId/tasks."""

from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from ..serializers import TaskSerializer
from ..services import task_list_service
from ..services.exceptions import ProjectNotVisible
from ._session import not_authenticated, session_user

FILTER_NAMES = ("status_id", "priority_id", "assignee_id")


class TaskListView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, project_id):
        user = session_user(request)

        if user is None:
            return not_authenticated()

        filters = {
            name: _filter_id(request, name)
            for name in FILTER_NAMES
        }

        try:
            tasks = task_list_service.list_project_tasks(
                project_id=project_id,
                user=user,
                **filters,
            )
        except ProjectNotVisible:
            return Response(
                {"detail": "Not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(TaskSerializer(tasks, many=True).data)


def _filter_id(request, name):
    raw = request.query_params.get(name)

    if raw is None:
        return None

    try:
        return int(raw)
    except (TypeError, ValueError):
        raise ValidationError({name: "Must be an integer."})
