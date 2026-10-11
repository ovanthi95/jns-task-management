"""Application logic for reading project membership."""

from data_access.projects.get_project_members import get_project_members
from users.services.permission_service import actor_has_permission


class ProjectMembersPermissionError(Exception):
    pass


class ProjectMembersNotFound(Exception):
    pass


def list_project_members(actor, project_id):
    if actor is None or not actor_has_permission(actor, "edit_projects"):
        raise ProjectMembersPermissionError(
            "Project editing permission required."
        )

    members = get_project_members(
        project_id=project_id,
        organisation_id=actor["organisation_id"],
    )

    if not members:
        raise ProjectMembersNotFound

    return members
