"""Who may reach a project, shared by API 06 and API 07.

Owner: Edward

The Task table has no organisation_id column, so a task belongs to an
organisation through its project. Both task services therefore have to answer
the same question before they touch a task row: may this caller see this
project at all?

Two conditions, both required:

  * the project is in the caller's own organisation, and
  * the caller holds a project_members row for it.

Membership is explicit. A project's created_by is not treated as implicit
membership here, because writing that membership row belongs to the
project-creation service (API 04), not to this one.

Failing either condition raises ProjectNotVisible, which the endpoints answer
with 404 rather than 403. A project in another organisation, a project the
caller is not a member of, and a project id that does not exist are all
indistinguishable from outside. A 403 would confirm the project exists, which
tells an attacker something about a tenant they cannot see.

`user` is the session dict sp_get_session_user returned, the same value APIs
02, 03, 04, 05 and 10 pass around, not a Django model instance. See
tasks/api/_session.py for why the task endpoints read the session rather than
request.user.
"""

from data_access.tasks.get_project_user_access import get_project_user_access

from .exceptions import ProjectNotVisible


def require_visible_project(*, project_id, user):
    """Return the project access row, or raise ProjectNotVisible.

    The returned dict carries project_organisation_id, which API 06 needs
    again when it checks the assignee, so the caller does not have to look the
    project up a second time.
    """
    access = get_project_user_access(
        project_id=project_id,
        user_id=user["user_id"],
    )

    if access is None:
        raise ProjectNotVisible()

    if access["project_organisation_id"] != user["organisation_id"]:
        raise ProjectNotVisible()

    permissions = set(getattr(user, "permissions", []) or [])

    if not access["is_member"] and "view_all_projects" not in permissions:
        raise ProjectNotVisible()

    return access
