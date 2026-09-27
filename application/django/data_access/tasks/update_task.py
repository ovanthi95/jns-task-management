"""API 08 data access."""

from ._procedure import call_procedure

PROCEDURE_NAME = "sp_update_task"


def update_task(*, task_id, organisation_id, changed_by, changes):
    rows = call_procedure(
        PROCEDURE_NAME,
        [
            task_id,
            organisation_id,
            changed_by,
            int("title" in changes),
            changes.get("title"),
            int("description" in changes),
            changes.get("description"),
            int("task_type_id" in changes),
            changes.get("task_type_id"),
            int("priority_id" in changes),
            changes.get("priority_id"),
            int("assignee_id" in changes),
            changes.get("assignee_id"),
            int("start_date" in changes),
            changes.get("start_date"),
            int("due_date" in changes),
            changes.get("due_date"),
            int("estimated_hours" in changes),
            changes.get("estimated_hours"),
            int("status_id" in changes),
            changes.get("status_id"),
        ],
    )

    return rows[0]["task_id"] if rows else task_id
