"""API 12 user update application logic."""

from django.db import transaction

from audit.services.history_recording import record_history
from data_access.users.update_user import update_user
from users.models import User


def edit_user(*, actor, user_id, changes):
    current_user = (
        User.objects
        .select_related("role")
        .filter(
            user_id=user_id,
            organisation_id=actor["organisation_id"],
        )
        .first()
    )

    if current_user is None:
        return update_user(
            user_id=user_id,
            organisation_id=actor["organisation_id"],
            changes=changes,
        )

    current = {
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "email": current_user.email,
        "role_id": current_user.role_id,
        "role": current_user.role.role_name if current_user.role else None,
        "availability": current_user.availability,
        "status": current_user.status,
    }

    with transaction.atomic():
        updated = update_user(
            user_id=user_id,
            organisation_id=actor["organisation_id"],
            changes=changes,
        )

        entity_name = (
            f"{updated['first_name']} {updated['last_name']}"
        ).strip()

        for field_name in (
            "first_name",
            "last_name",
            "email",
            "availability",
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
                entity_type="User",
                entity_id=user_id,
                entity_name=entity_name,
                action="Updated",
                field_name=field_name,
                old_value=old_value,
                new_value=new_value,
                description=f'Updated user "{entity_name}".',
            )

        if (
            "role_id" in changes
            and current["role_id"] != updated["role_id"]
        ):
            record_history(
                organisation_id=actor["organisation_id"],
                user_id=actor["user_id"],
                entity_type="User",
                entity_id=user_id,
                entity_name=entity_name,
                action="Updated",
                field_name="role",
                old_value=current["role"],
                new_value=updated["role_name"],
                description=f'Updated user "{entity_name}".',
            )

        return updated
