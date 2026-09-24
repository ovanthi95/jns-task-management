# API 05 - Project list application logic
# Owner: Jessie

from data_access.projects.get_projects import get_projects


class ProjectListError(Exception):
    """Base exception for project list errors."""
    pass


class ProjectListPermissionError(ProjectListError):
    """Raised when the authenticated user is invalid."""
    pass


def get_project_list(current_user):
    if current_user is None:
        raise ProjectListPermissionError(
            "Authentication required."
        )

    organisation_id = current_user.get("organisation_id")

    if not organisation_id:
        raise ProjectListPermissionError(
            "Invalid authenticated user."
        )

    return get_projects(organisation_id)