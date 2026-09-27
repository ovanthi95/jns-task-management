"""API 08 support data access."""

from ._procedure import call_procedure

PROCEDURE_NAME = "sp_get_task_status"


def get_task_status(status_id):
    rows = call_procedure(PROCEDURE_NAME, [status_id])
    return rows[0] if rows else None
