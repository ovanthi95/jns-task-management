"""API 06 data access

Owner: Edward
This module must call exactly one stored procedure: sp_create_task.
Do not put application/business logic here.
"""

from ._procedure import call_procedure

PROCEDURE_NAME = "sp_create_task"


def create_task(
    *,
    project_id,
    task_type_id,
    status_id,
    priority_id,
    title,
    description,
    start_date,
    due_date,
    estimated_hours,
    assignee_user_id,
    created_by,
):
    """Insert one task and its first assignment, and return the new task_id.

    Every value is passed through as given. Validation, permissions and the
    organisation check belong to the service layer; project_id and created_by
    are already resolved from the session by the time they arrive here.

    The procedure writes two rows, so the caller must run this inside
    transaction.atomic() to make sure a failure cannot leave a task with no
    assignee.
    """
    rows = call_procedure(
        PROCEDURE_NAME,
        [
            project_id,
            task_type_id,
            status_id,
            priority_id,
            title,
            description,
            start_date,
            due_date,
            estimated_hours,
            assignee_user_id,
            created_by,
        ],
    )

    return rows[0]["task_id"]
