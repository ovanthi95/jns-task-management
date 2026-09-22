"""Views for API 02 and API 03.

    API 02  GET  /api/users   list users in the caller's organisation
    API 03  POST /api/users   create a user in the caller's organisation

Both are scoped to the caller's organisation. The organisation is never taken
from the request, only from the authenticated user.

Who can call
------------
API 02 is open to Admin and Manager, because they assign tasks and need the
team list. API 03 is Admin only. Any other role gets 403. Both rules are
properties of the caller alone, not of any row, so 403 leaks nothing.
Confirmed with Ovanthi, 22 Sep 2026.
"""

from rest_framework import permissions

# Matched case-insensitively against Role.role_name, same approach as
# tasks.views.TASK_CREATOR_ROLES. Seeded values are Admin, Manager,
# Employee, Intern and Volunteer.
USER_LIST_ROLES = frozenset({"admin", "manager"})
USER_CREATE_ROLES = frozenset({"admin"})


def _role_name(request):
    """The caller's role name in lower case, or None if there is no role."""

    role = getattr(request.user, "role", None)

    if role is None:
        return None

    return role.role_name.lower()


class CanListUsers(permissions.BasePermission):
    """The role restriction on API 02 (GET)."""

    message = "Your role is not permitted to list users."

    def has_permission(self, request, view):
        if request.method != "GET":
            return True

        return _role_name(request) in USER_LIST_ROLES


class CanCreateUser(permissions.BasePermission):
    """The role restriction on API 03 (POST)."""

    message = "Your role is not permitted to create users."

    def has_permission(self, request, view):
        if request.method != "POST":
            return True

        return _role_name(request) in USER_CREATE_ROLES