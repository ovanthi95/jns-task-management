"""API 07 data access

Owner: Edward
This module must call exactly one stored procedure: sp_get_project_tasks.
Do not put application/business logic here.
"""

import json
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

    The filters are optional. Passing None means "do not filter on this"; the
    procedure ANDs together whichever ones are given.

    task_id is not a client filter. API 06 passes it to read back the row it
    has just written, so the created task and a listed task come out of the
    same query in the same shape.

    Permissions are not checked here. The service layer has already decided
    that the caller may see this project.

    Two things are normalised before the rows leave this module, both of them
    driver artefacts rather than business rules:

      * the assignees column arrives as a JSON string, or NULL when the task
        has nobody assigned, and is returned as a list;
      * created_at and updated_at arrive naive because the driver carries no
        timezone. The columns hold UTC and the project runs with
        USE_TZ = True, so UTC is attached back.
    """
    rows = call_procedure(
        PROCEDURE_NAME,
        [project_id, status_id, priority_id, assignee_id, task_id],
    )

    return [_normalise(row) for row in rows]


def _normalise(row):
    row["assignees"] = _parse_assignees(row.get("assignees"))

    for column in ("created_at", "updated_at"):
        row[column] = _as_utc(row.get(column))

    return row


def _parse_assignees(value):
    if value is None:
        return []

    if isinstance(value, (bytes, bytearray)):
        value = value.decode("utf-8")

    if isinstance(value, str):
        return json.loads(value)

    # Some driver versions decode JSON columns for us.
    return value


def _as_utc(value):
    if value is None or value.tzinfo is not None:
        return value

    return value.replace(tzinfo=timezone.utc)
