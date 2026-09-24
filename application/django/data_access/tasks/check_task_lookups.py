"""API 06 data access (support call)

Owner: Edward
This module must call exactly one stored procedure: sp_check_task_lookups.
Do not put application/business logic here.
"""

from ._procedure import call_procedure

PROCEDURE_NAME = "sp_check_task_lookups"


def check_task_lookups(*, task_type_id, status_id, priority_id):
    """Report which of the three lookup ids exist.

    Returns a dict with the boolean keys task_type_exists, status_exists and
    priority_exists. All three are reported every time, so the service can
    name every bad field in one 400 instead of one per request.
    """
    row = call_procedure(
        PROCEDURE_NAME,
        [task_type_id, status_id, priority_id],
    )[0]

    return {key: bool(value) for key, value in row.items()}
