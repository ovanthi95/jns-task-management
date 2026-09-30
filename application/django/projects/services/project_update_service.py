"""Application logic for project lifecycle updates."""

from django.contrib.auth.hashers import check_password
from django.db import transaction

from audit.services.history_recording import record_history
from data_access.projects.update_project import update_project
from projects.models import Project
from users.models import User


class ProjectNotFound(Exception):
    pass


class ReactivationPasswordRequired(Exception):
    pass


class InvalidAdminPassword(Exception):
    pass


def edit_project(*, actor, project_id, changes, admin_password=None):
    current = (
        Project.objects
        .filter(
            project_id=project_id,
            organisation_id=actor["organisation_id"],
        )
        .values(
            "project_name",
            "description",
            "start_date",
            "end_date",
            "status",
        )
        .first()
    )

    if current is None:
        raise ProjectNotFound

    requested_status = changes.get("status")

    if (
        current["status"] == "Completed"
        and requested_status
        and requested_status != "Completed"
    ):
        if not admin_password:
            raise ReactivationPasswordRequired

        password_hash = (
            User.objects
            .filter(
                user_id=actor["user_id"],
                organisation_id=actor["organisation_id"],
            )
            .values_list("password", flat=True)
            .first()
        )

        if not password_hash or not check_password(admin_password, password_hash):
            raise InvalidAdminPassword

    with transaction.atomic():
        updated = update_project(
            project_id=project_id,
            organisation_id=actor["organisation_id"],
            changes=changes,
        )

        entity_name = updated["project_name"]

        for field_name in (
            "project_name",
            "description",
            "start_date",
            "end_date",
            "status",
        ):
            if field_name not in changes:
                continue

            old_value = current.get(field_name)
            new_value = updated.get(field_name)

            if old_value == new_value:
                continue

            record_history(
                organisation_id=actor["organisation_id"],
                user_id=actor["user_id"],
                entity_type="Project",
                entity_id=project_id,
                entity_name=entity_name,
                action="Updated",
                field_name=field_name,
                old_value=old_value,
                new_value=new_value,
                description=f'Updated project "{entity_name}".',
            )

        return updated
