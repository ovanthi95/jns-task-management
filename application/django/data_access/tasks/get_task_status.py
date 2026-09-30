"""API 08 support data access.

Returns one active task status by id. This module calls exactly one stored
procedure so API 08 can enforce the "assignee may only complete" rule without
using the ORM.
"""

from ._procedure import call_procedure

PROCEDURE_NAME = "sp_get_task_status"


def get_task_status(status_id):
    rows = call_procedure(PROCEDURE_NAME, [status_id])

    return rows[0] if rows else None
