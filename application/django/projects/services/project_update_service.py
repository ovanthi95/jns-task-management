"""Application logic for project lifecycle and membership updates."""

from django.contrib.auth.hashers import check_password
from django.db import transaction

from audit.services.history_recording import record_history
from data_access.projects.get_project_members import get_project_members
from data_access.projects.get_projects import get_projects
from data_access.projects.update_project import update_project
from data_access.projects.update_project_members import update_project_members
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

    member_ids = changes.get("member_ids")
    detail_changes = {
        field_name: value
        for field_name, value in changes.items()
        if field_name != "member_ids"
    }

    with transaction.atomic():
        current_members = []
        if member_ids is not None:
            current_members = get_project_members(
                project_id=project_id,
                organisation_id=actor["organisation_id"],
            )

        if detail_changes:
            updated = update_project(
                project_id=project_id,
                organisation_id=actor["organisation_id"],
                changes=detail_changes,
            )
        else:
            updated = next(
                (
                    project
                    for project in get_projects(
                        actor["organisation_id"],
                        user_id=actor["user_id"],
                        can_view_all=True,
                    )
                    if int(project["project_id"]) == int(project_id)
                ),
                None,
            )

            if updated is None:
                raise ProjectNotFound

        for field_name in (
            "project_name",
            "description",
            "start_date",
            "end_date",
            "status",
        ):
            if field_name not in detail_changes:
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
                entity_name=updated["project_name"],
                action="Updated",
                field_name=field_name,
                old_value=old_value,
                new_value=new_value,
                description=f'Updated project "{updated["project_name"]}".',
            )

        if member_ids is not None:
            updated_members = update_project_members(
                project_id=project_id,
                organisation_id=actor["organisation_id"],
                member_ids=member_ids,
            )

            old_member_ids = {
                int(member["user_id"])
                for member in current_members
            }
            new_member_ids = {
                int(member["user_id"])
                for member in updated_members
            }

            added = [
                f'{member["first_name"]} {member["last_name"]}'
                for member in updated_members
                if int(member["user_id"]) not in old_member_ids
            ]
            removed = [
                f'{member["first_name"]} {member["last_name"]}'
                for member in current_members
                if int(member["user_id"]) not in new_member_ids
            ]

            if added or removed:
                record_history(
                    organisation_id=actor["organisation_id"],
                    user_id=actor["user_id"],
                    entity_type="Project",
                    entity_id=project_id,
                    entity_name=updated["project_name"],
                    action="Updated",
                    field_name="members",
                    old_value=removed,
                    new_value=added,
                    description=f'Updated members for project "{updated["project_name"]}".',
                )

        return updated
