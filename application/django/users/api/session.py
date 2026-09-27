from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from users.services.session_service import get_authenticated_session_user


@method_decorator(ensure_csrf_cookie, name="dispatch")
class SessionView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        user_id = request.session.get("user_id")
        user = get_authenticated_session_user(user_id) if user_id else None

        if user is None:
            if user_id:
                request.session.flush()

            return Response(
                {"detail": "Not authenticated."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        return Response(
            {"user": user},
            status=status.HTTP_200_OK,
        )
