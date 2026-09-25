"""DRF authentication for the JNS session convention.

API 01 stores the signed-in user's id in request.session["user_id"]. Django's
stock AuthenticationMiddleware looks for a different session key, so without
this adapter DRF's IsAuthenticated sees API 06/07 callers as anonymous.
"""

from rest_framework.authentication import SessionAuthentication

from users.models import User


class JNSSessionAuthentication(SessionAuthentication):
    """Turn the JNS user_id session value into request.user."""

    def authenticate(self, request):
        user_id = request.session.get("user_id")

        if not user_id:
            return None

        user = (
            User.objects
            .select_related("organisation", "role")
            .filter(
                user_id=user_id,
                status__iexact="Active",
                organisation__status__iexact="Active",
                organisation__organisation_name__iexact="JNS Business Solutions",
            )
            .first()
        )

        if user is None:
            request.session.flush()
            return None

        # Same CSRF protection as DRF's normal SessionAuthentication.
        self.enforce_csrf(request)

        return (user, None)

    def authenticate_header(self, request):
        # Makes unauthenticated IsAuthenticated responses use 401 rather than
        # silently looking like an authorisation failure.
        return "Session"
