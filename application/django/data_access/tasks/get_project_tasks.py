"""API 07 data access

Owner: Edward
This module must call exactly one stored procedure: sp_get_project_tasks.
Do not put application/business logic here.
"""

from datetime import timezone

from ._procedure import call_procedure

PROCEDURE_NAME = "sp_get_project_tasks"


def get_project_tasks(
    *,
    project_id,
    status_id=None,
    priority_id=None,
    assignee_id=None,
    task_id=None,
):
    """Return the tasks of one project, newest first.

    The stored procedure returns normal relational rows. A task with multiple
    assignees therefore appears more than once, and this module groups those
    rows back into one task dictionary with an assignees list.

    The filters are optional. Passing None means "do not filter on this"; the
    procedure ANDs together whichever ones are given.

    task_id is not a client filter. API 06 passes it to read back the row it
    has just written, so the created task and a listed task come out of the
    same query in the same shape.

    Permissions are not checked here. The service layer has already decided
    that the caller may see this project.

    created_at and updated_at arrive naive because the driver carries no
    timezone. The columns hold UTC and the project runs with USE_TZ = True,
    so UTC is attached back.
    """
    rows = call_procedure(
        PROCEDURE_NAME,
        [project_id, status_id, priority_id, assignee_id, task_id],
    )

    return _group_tasks(rows)


def _group_tasks(rows):
    tasks = []
    by_task_id = {}

    for row in rows:
        task_id = row["task_id"]

        if task_id not in by_task_id:
            task = {
                key: value
                for key, value in row.items()
                if key
                not in {
                    "assignee_user_id",
                    "assignee_first_name",
                    "assignee_last_name",
                    "assignee_assignment_role",
                    "task_assignee_id",
                }
            }
            task["assignees"] = []

            for column in ("created_at", "updated_at"):
                task[column] = _as_utc(task.get(column))

            by_task_id[task_id] = task
            tasks.append(task)

        assignee_user_id = row.get("assignee_user_id")
        if assignee_user_id is not None:
            by_task_id[task_id]["assignees"].append(
                {
                    "user_id": assignee_user_id,
                    "first_name": row.get("assignee_first_name"),
                    "last_name": row.get("assignee_last_name"),
                    "assignment_role": row.get("assignee_assignment_role"),
                }
            )

    return tasks


def _as_utc(value):
    if value is None or value.tzinfo is not None:
        return value

    return value.replace(tzinfo=timezone.utc)
