"""GET /api/projects/:projectId/members."""

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from projects.services.project_members_service import (
    ProjectMembersNotFound,
    ProjectMembersPermissionError,
    list_project_members,
)


class ProjectMembersView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, project_id):
        from users.services.session_service import get_authenticated_session_user

        actor = get_authenticated_session_user(request.session.get("user_id"))

        if actor is None:
            request.session.flush()
            return Response(
                {"detail": "Not authenticated."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            members = list_project_members(actor, project_id)
        except ProjectMembersPermissionError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_403_FORBIDDEN,
            )
        except ProjectMembersNotFound:
            return Response(
                {"detail": "Project not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {"members": members},
            status=status.HTTP_200_OK,
        )
