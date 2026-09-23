from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from users.services.session_service import get_authenticated_session_user


class SessionView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        user_id = request.session.get("user_id")

        if not user_id:
            return Response(
                {"detail": "Not authenticated."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        user = get_authenticated_session_user(user_id)

        if user is None:
            # Session points to a user that is no longer valid/active.
            request.session.flush()

            return Response(
                {"detail": "Not authenticated."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        return Response(
            {"user": user},
            status=status.HTTP_200_OK,
        )
    