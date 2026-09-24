# API 02 - Users list
# Owner: Manatka

from data_access.users.get_users import get_users

# Matched case-insensitively against role_name from sp_get_session_user.
# Seeded roles: Admin, Manager, Employee, Intern, Volunteer.
USER_LIST_ROLES = frozenset({"admin", "manager"})


def can_list_users(session_user):
    """Admin and Manager assign tasks, so they may read the team list."""

    role_name = (session_user or {}).get("role_name") or ""

    return role_name.lower() in USER_LIST_ROLES


def list_users(session_user):
    """Users in the caller's organisation.

    The organisation is taken from the session user, never from the request.
    Raises PermissionError when the caller's role is not allowed; the API
    layer maps that to 403.
    """

    if not can_list_users(session_user):
        raise PermissionError("Your role is not permitted to list users.")

    return get_users(session_user["organisation_id"])