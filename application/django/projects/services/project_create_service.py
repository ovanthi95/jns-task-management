# API 04 - Project creation application logic
# Owner: Jessie

from data_access.projects.create_project import create_project


class ProjectCreateError(Exception):
    """Base exception for project creation errors."""
    pass


class ProjectValidationError(ProjectCreateError):
    """Raised when project input is invalid."""
    pass


class ProjectPermissionError(ProjectCreateError):
    """Raised when the user is not allowed to create projects."""
    pass


def create_project_service(
    current_user,
    project_name,
    description=None,
    start_date=None,
    end_date=None,
    member_ids=None
):
    # The user must be authenticated.
    if current_user is None:
        raise ProjectPermissionError(
            "Authentication required."
        )

    # Only Admin or Manager can create a project.
    role_name = current_user.get("role_name", "")

    if role_name.lower() not in ("admin", "manager"):
        raise ProjectPermissionError(
            "Only Admin or Manager can create a project."
        )

    # Project name is required.
    if not project_name or not project_name.strip():
        raise ProjectValidationError(
            "Project name is required."
        )

    project_name = project_name.strip()

    # Project model allows a maximum of 150 characters.
    if len(project_name) > 150:
        raise ProjectValidationError(
            "Project name must not exceed 150 characters."
        )

    # Validate project dates.
    if start_date and end_date and start_date > end_date:
        raise ProjectValidationError(
            "Start date cannot be after end date."
        )

    # Members are optional.
    if member_ids is None:
        member_ids = []

    if not isinstance(member_ids, list):
        raise ProjectValidationError(
            "member_ids must be a list."
        )

    # Every member ID must be an integer.
    if any(
        not isinstance(member_id, int)
        or isinstance(member_id, bool)
        for member_id in member_ids
    ):
        raise ProjectValidationError(
            "Each member ID must be an integer."
        )

    # The same user cannot be added twice.
    if len(member_ids) != len(set(member_ids)):
        raise ProjectValidationError(
            "Duplicate member IDs are not allowed."
        )

    # These values come from the authenticated session user,
    # not from the request body.
    organisation_id = current_user.get("organisation_id")
    created_by = current_user.get("user_id")

    if not organisation_id or not created_by:
        raise ProjectPermissionError(
            "Invalid authenticated user."
        )

    return create_project(
        organisation_id=organisation_id,
        project_name=project_name,
        description=description,
        start_date=start_date,
        end_date=end_date,
        created_by=created_by,
        member_ids=member_ids
    )