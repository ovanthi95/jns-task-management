"""Workload reporting APIs."""

from django.db import DatabaseError
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from users.services.permission_service import actor_has_permission
from users.services.session_service import get_authenticated_session_user
from users.services.workload_service import (
    list_user_workload_tasks,
    list_workload,
)


def workload_actor(request):
    actor = get_authenticated_session_user(
        request.session.get("user_id")
    )

    if actor is None:
        request.session.flush()
        return None, Response(
            {"detail": "Not authenticated."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if not actor_has_permission(actor, "view_workload"):
        return None, Response(
            {"detail": "Workload permission required."},
            status=status.HTTP_403_FORBIDDEN,
        )

    return actor, None


class WorkloadView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        actor, error = workload_actor(request)
        if error is not None:
            return error

        return Response({
            "due_soon_days": 7,
            "users": list_workload(actor=actor),
        })


class UserWorkloadTasksView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, user_id):
        actor, error = workload_actor(request)
        if error is not None:
            return error

        try:
            rows = list_user_workload_tasks(
                actor=actor,
                user_id=user_id,
            )
        except DatabaseError as exc:
            if "user not found" in str(exc).lower():
                return Response(
                    {"detail": "User not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            raise

        return Response(rows)
