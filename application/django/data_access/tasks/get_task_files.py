"""Read persisted task attachment metadata."""

from ._procedure import call_procedure

PROCEDURE_NAME = "sp_get_task_files"


def get_task_files(task_id):
    return call_procedure(PROCEDURE_NAME, [task_id])
