# API 04 - Project creation application logic
# Owner: Jessie

from django.db import transaction

from audit.services.history_recording import record_history
from data_access.projects.create_project import create_project
from users.services.permission_service import actor_has_permission


class ProjectCreateError(Exception):
    pass


class ProjectValidationError(ProjectCreateError):
    pass


class ProjectPermissionError(ProjectCreateError):
    pass


def create_project_service(
    current_user,
    project_name,
    description=None,
    start_date=None,
    end_date=None,
    member_ids=None
):
    if current_user is None:
        raise ProjectPermissionError("Authentication required.")

    if not actor_has_permission(current_user, "create_projects"):
        raise ProjectPermissionError(
            "Project creation permission required."
        )

    if not project_name or not project_name.strip():
        raise ProjectValidationError("Project name is required.")

    project_name = project_name.strip()

    if len(project_name) > 150:
        raise ProjectValidationError(
            "Project name must not exceed 150 characters."
        )

    if start_date and end_date and start_date > end_date:
        raise ProjectValidationError(
            "Start date cannot be after end date."
        )

    if member_ids is None:
        member_ids = []

    if not isinstance(member_ids, list):
        raise ProjectValidationError("member_ids must be a list.")

    if any(
        not isinstance(member_id, int)
        or isinstance(member_id, bool)
        for member_id in member_ids
    ):
        raise ProjectValidationError(
            "Each member ID must be an integer."
        )

    organisation_id = current_user.get("organisation_id")
    created_by = current_user.get("user_id")

    if not organisation_id or not created_by:
        raise ProjectPermissionError("Invalid authenticated user.")

    # The creator must always be able to enter the project they just created.
    member_ids = list(dict.fromkeys([created_by, *member_ids]))

    with transaction.atomic():
        created = create_project(
            organisation_id=organisation_id,
            project_name=project_name,
            description=description,
            start_date=start_date,
            end_date=end_date,
            created_by=created_by,
            member_ids=member_ids
        )

        record_history(
            organisation_id=organisation_id,
            user_id=created_by,
            entity_type="Project",
            entity_id=created["project_id"],
            entity_name=created["project_name"],
            action="Created",
            new_value={
                "project_name": created["project_name"],
                "description": created.get("description"),
                "status": created.get("status"),
                "start_date": created.get("start_date"),
                "end_date": created.get("end_date"),
            },
            description=f'Created project "{created["project_name"]}".',
        )

        return created
