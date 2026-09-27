"""Read the signed-in user from the custom Django session."""

from rest_framework import status
from rest_framework.response import Response

from users.services.session_service import get_authenticated_session_user


def session_user(request):
    user_id = request.session.get("user_id")

    if not user_id:
        return None

    user = get_authenticated_session_user(user_id)

    if user is None:
        request.session.flush()

    return user


def not_authenticated():
    return Response(
        {"detail": "Not authenticated."},
        status=status.HTTP_401_UNAUTHORIZED,
    )
