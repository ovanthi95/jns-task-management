"""API 11 - GET /api/tasks/:taskId/audit."""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from audit.services.task_audit_service import (
    TaskAuditNotFound,
    list_task_audit,
)


class TaskAuditView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, task_id):
        try:
            rows = list_task_audit(
                actor_user_id=request.user.user_id,
                task_id=task_id,
            )
        except TaskAuditNotFound:
            return Response(
                {"detail": "Not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(rows, status=status.HTTP_200_OK)
