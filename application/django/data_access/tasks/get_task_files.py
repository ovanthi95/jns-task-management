"""Read persisted task attachment metadata."""

from ._procedure import call_procedure

PROCEDURE_NAME = "sp_get_task_files"


def get_task_files(task_id):
    return call_procedure(PROCEDURE_NAME, [task_id])


def get_task_file(task_id, attachment_id):
    """Return one attachment from the task, including its private storage key."""
    rows = get_task_files(task_id)
    attachment_id = int(attachment_id)

    return next(
        (row for row in rows if int(row["attachment_id"]) == attachment_id),
        None,
    )
