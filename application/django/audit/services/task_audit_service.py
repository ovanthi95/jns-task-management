"""API 11 task audit application logic."""

import json

from data_access.audit.get_task_audit import get_task_audit
from data_access.tasks.get_task_access import get_task_access


class TaskAuditNotFound(Exception):
    """No such task, or the caller may not see that it exists."""


def _normalise_json(value):
    if value is None or isinstance(value, (dict, list, int, float, bool)):
        return value

    if isinstance(value, (bytes, bytearray)):
        value = value.decode("utf-8")

    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value

    return value


def list_task_audit(*, actor_user_id, task_id):
    if get_task_access(task_id, actor_user_id) is None:
        raise TaskAuditNotFound()

    rows = get_task_audit(task_id=task_id)

    for row in rows:
        row["old_value"] = _normalise_json(row.get("old_value"))
        row["new_value"] = _normalise_json(row.get("new_value"))

    return rows
