# API 05 - GET /api/projects
# Owner: Jessie

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from projects.services.project_list_service import (
    ProjectListPermissionError,
    get_project_list,
)
from users.services.session_service import get_authenticated_session_user


class ProjectListView(APIView):

    def get(self, request):
        user_id = request.session.get("user_id")

        if not user_id:
            return Response(
                {"detail": "Authentication required."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        current_user = get_authenticated_session_user(user_id)

        if current_user is None:
            request.session.flush()
            return Response(
                {"detail": "Authentication required."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            projects = get_project_list(current_user)
        except ProjectListPermissionError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(projects, status=status.HTTP_200_OK)
