# API 02 - Users list
# Owner: Manatka
# GET /api/users

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from users.services.session_service import get_authenticated_session_user
from users.services.user_list_service import list_users


class UserListView(APIView):
    """Same session convention as users/api/session.py.

    401 when there is no valid session, 403 when the role is not allowed,
    200 with a JSON array of users otherwise. password_hash never appears
    because sp_get_users does not select it.
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        user_id = request.session.get("user_id")

        if not user_id:
            return Response(
                {"detail": "Not authenticated."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        session_user = get_authenticated_session_user(user_id)

        if session_user is None:
            request.session.flush()

            return Response(
                {"detail": "Not authenticated."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            users = list_users(session_user)
        except PermissionError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)

        return Response(users, status=status.HTTP_200_OK)