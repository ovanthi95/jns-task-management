"""API 12 user update persistence."""

from data_access.tasks._procedure import call_procedure

PROCEDURE_NAME = "sp_update_user"


def update_user(*, user_id, organisation_id, changes):
    rows = call_procedure(
        PROCEDURE_NAME,
        [
            user_id,
            organisation_id,
            int("first_name" in changes),
            changes.get("first_name"),
            int("last_name" in changes),
            changes.get("last_name"),
            int("email" in changes),
            changes.get("email"),
            int("role_id" in changes),
            changes.get("role_id"),
            int("availability" in changes),
            changes.get("availability"),
            int("status" in changes),
            changes.get("status"),
        ],
    )

    return rows[0] if rows else None
