"""Reading the caller out of the session, shared by the task endpoints.

Owner: Edward

This module holds no business logic and calls no stored procedure of its own.
It exists so that the task endpoint modules do not each repeat the same ten
lines of session handling.

Why the task endpoints do this at all
-------------------------------------
API 01 authenticates by putting the user id in the Django session and nothing
else:

    request.session["user_id"] = user["user_id"]

It never calls django.contrib.auth.login(), so request.user stays
AnonymousUser for every request the React client makes. An endpoint guarded by
permissions.IsAuthenticated therefore refuses every real browser session, and
an endpoint reading request.user gets an anonymous user rather than the person
who logged in.

APIs 02, 03, 04, 05 and 10 already read the session directly through
users.services.session_service. The task endpoints now do the same, so there
is one convention across the whole API rather than two.

Resolving the id through sp_get_session_user on each request, rather than
trusting the cookie alone, is what makes a session stop working the moment the
user is suspended, deleted, or moved out of the organisation. The cookie
outlives all three.

Private by convention (leading underscore): nothing outside tasks/api/ should
import it.
"""

from rest_framework import status
from rest_framework.response import Response

from users.services.session_service import get_authenticated_session_user

def session_user(request):
    """Return the caller as a dict, or None when there is no valid session.

    The dict is whatever sp_get_session_user selected:

        user_id, first_name, last_name, email, status,
        organisation_id, role_id, role_name, organisation_name

    A cookie that names a user who is no longer active resolves to None, and
    the stale session is flushed on the way out so the next request does not
    repeat the lookup.
    """
    user_id = request.session.get("user_id")

    if not user_id:
        return None

    user = get_authenticated_session_user(user_id)

    if user is None:
        request.session.flush()

    return user


def not_authenticated():
    """The 401 body, built fresh each time.

    A Response object carries rendering state once it has been returned, so a
    single shared instance cannot be reused across requests.
    """
    return Response(
        {"detail": "Not authenticated."},
        status=status.HTTP_401_UNAUTHORIZED,
    )
