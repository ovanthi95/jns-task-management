"""API 11 task audit persistence."""

from data_access.tasks._procedure import call_procedure

PROCEDURE_NAME = "sp_get_task_audit"


def get_task_audit(*, task_id):
    return call_procedure(PROCEDURE_NAME, [task_id])
