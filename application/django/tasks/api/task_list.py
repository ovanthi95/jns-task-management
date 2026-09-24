"""API 07 - GET /api/projects/:projectId/tasks

Code owner: Edward

The HTTP layer for the list service. It reads the three optional filters off
the query string, turns them into integers, calls one service and renders what
comes back. Nothing here touches the database, the ORM or a stored procedure.

Parsing a filter and applying it are two different jobs. "?status_id=abc" is a
malformed request, which is this module's problem, so it is answered with 400
here. "?status_id=999" is a well-formed request that happens to select nothing,
which is the service's problem, and it is answered with an empty 200.

Status codes this endpoint can answer with:

    200  the project's tasks, newest first, possibly an empty list
    400  a filter was present but was not a number
    401  no session
    404  the project does not exist, or this caller may not see that it does
"""

from rest_framework import permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from ..serializers import TaskSerializer
from ..services import task_list_service
from ..services.exceptions import ProjectNotVisible

FILTER_NAMES = ("status_id", "priority_id", "assignee_id")


class TaskListView(APIView):
    """API 07. Open to any member of the project, whatever their role."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, project_id):
        filters = _read_filters(request)

        try:
            tasks = task_list_service.list_project_tasks(
                project_id=project_id,
                user=request.user,
                **filters,
            )
        except ProjectNotVisible:
            return Response(
                {"detail": "Not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Through the read serializer for the same reason API 06 does it: the
        # decimals have to stay strings and the timestamps have to keep their
        # "Z".
        return Response(TaskSerializer(tasks, many=True).data)


def _read_filters(request):
    """All three filters at once, so a malformed value is answered the same way.

    An absent filter is None rather than missing, because the service takes
    all three every time and treats None as "do not narrow on this".
    """

    return {
        name: _filter_id(request, name)
        for name in FILTER_NAMES
    }


def _filter_id(request, name):
    """One query parameter as an int, or 400 if it is not a number.

    Without this a value like "abc" would reach the stored procedure, which
    would fail on the type and surface as a 500 rather than a bad request.
    """

    raw = request.query_params.get(name)

    if raw is None:
        return None

    try:
        return int(raw)
    except (TypeError, ValueError):
        raise ValidationError({name: "Must be an integer."})
