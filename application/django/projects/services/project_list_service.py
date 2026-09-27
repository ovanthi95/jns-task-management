# API 05 - Project list application logic
# Owner: Jessie

from data_access.projects.get_projects import get_projects
from users.services.permission_service import actor_has_permission


class ProjectListError(Exception):
    pass


class ProjectListPermissionError(ProjectListError):
    pass


def get_project_list(current_user):
    if current_user is None:
        raise ProjectListPermissionError("Authentication required.")

    organisation_id = current_user.get("organisation_id")
    user_id = current_user.get("user_id")

    if not organisation_id or not user_id:
        raise ProjectListPermissionError(
            "Invalid authenticated user."
        )

    return get_projects(
        organisation_id,
        user_id=user_id,
        can_view_all=actor_has_permission(
            current_user,
            "view_all_projects",
        ),
    )
