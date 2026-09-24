"""API 06 and API 07 data access (shared support call)

Owner: Edward
This module must call exactly one stored procedure:
sp_get_project_user_access.
Do not put application/business logic here.

Both task endpoints need the same two facts before they touch any task row:
which organisation a project belongs to, and whether a given user is a member
of it. The caller asks about itself first, and API 06 asks again about the
chosen assignee. Deciding what those facts mean - 404 for the caller, 400 for
the assignee - is the service layer's job, not this module's.
"""

from ._procedure import call_procedure

PROCEDURE_NAME = "sp_get_project_user_access"


def get_project_user_access(*, project_id, user_id):
    """Return the project/user access facts, or None when no such project.

    On success the dict holds:
        project_id, project_organisation_id,
        user_id, user_organisation_id, is_member

    A project that does not exist gives None. A project that exists paired
    with a user_id that does not gives a dict whose user_id and
    user_organisation_id are None. Those two cases mean different things to
    the caller, so they are kept apart.
    """
    rows = call_procedure(PROCEDURE_NAME, [project_id, user_id])

    if not rows:
        return None

    row = rows[0]
    row["is_member"] = bool(row["is_member"])
    return row
