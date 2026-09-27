"""API 11 - GET /api/tasks/:taskId/audit."""

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from audit.services.task_audit_service import (
    TaskAuditNotFound,
    list_task_audit,
)
from tasks.api._session import not_authenticated, session_user


class TaskAuditView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, task_id):
        actor = session_user(request)

        if actor is None:
            return not_authenticated()

        try:
            rows = list_task_audit(
                actor_user_id=actor["user_id"],
                task_id=task_id,
            )
        except TaskAuditNotFound:
            return Response(
                {"detail": "Not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(rows, status=status.HTTP_200_OK)
