"""Shared project visibility checks for task APIs."""

from data_access.tasks.get_project_user_access import get_project_user_access

from .exceptions import ProjectNotVisible


def require_visible_project(*, project_id, user):
    access = get_project_user_access(
        project_id=project_id,
        user_id=user["user_id"],
    )

    if access is None:
        raise ProjectNotVisible()

    if access["project_organisation_id"] != user["organisation_id"]:
        raise ProjectNotVisible()

    if not access["is_member"]:
        raise ProjectNotVisible()

    return access
