"""DRF authentication for the JNS session convention.

API 01 stores the signed-in user's id in request.session["user_id"]. Django's
stock AuthenticationMiddleware looks for a different session key, so without
this adapter DRF's IsAuthenticated sees API 06/07 callers as anonymous.

The user is resolved through the existing sp_get_session_user data-access path,
not through the ORM, so authentication follows the same stored-procedure
architecture as the group APIs.
"""

from types import SimpleNamespace

from rest_framework.authentication import SessionAuthentication

from users.services.session_service import get_authenticated_session_user


class SessionPrincipal(SimpleNamespace):
    """Minimal request.user shape needed by the task services."""

    @property
    def is_authenticated(self):
        return True


class JNSSessionAuthentication(SessionAuthentication):
    """Turn the JNS user_id session value into request.user."""

    def authenticate(self, request):
        user_id = request.session.get("user_id")

        if not user_id:
            return None

        session_user = get_authenticated_session_user(user_id)

        if session_user is None:
            request.session.flush()
            return None

        self.enforce_csrf(request)

        role = SimpleNamespace(
            role_id=session_user["role_id"],
            role_name=session_user["role_name"],
        )

        principal = SessionPrincipal(
            user_id=session_user["user_id"],
            organisation_id=session_user["organisation_id"],
            role=role,
            permissions=list(session_user.get("permissions") or []),
            email=session_user["email"],
            first_name=session_user["first_name"],
            last_name=session_user["last_name"],
        )

        return (principal, None)

    def authenticate_header(self, request):
        return "Session"
