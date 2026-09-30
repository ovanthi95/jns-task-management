"""Read persisted task comments."""

from ._procedure import call_procedure

PROCEDURE_NAME = "sp_get_task_comments"


def get_task_comments(task_id):
    return call_procedure(PROCEDURE_NAME, [task_id])
