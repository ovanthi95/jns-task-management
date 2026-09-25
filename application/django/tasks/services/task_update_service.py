"""API 08 - task update application logic.

Rules used by the JNS group build:
- Admin: may edit task details, change any status, and reassign.
- Manager: may edit task details and change any status, but may not reassign.
- Employee / Intern / Volunteer: may only mark a task assigned to themselves
  as Completed.

The database write itself is performed by sp_update_task. Reads use the
existing task data-access functions so this service stays on the same
stored-procedure architecture as API 06/07/10.
"""

from django.db import transaction

from data_access.tasks.check_task_lookups import check_task_lookups
from data_access.tasks.get_project_tasks import get_project_tasks
from data_access.tasks.get_project_user_access import get_project_user_access
from data_access.tasks.get_task_access import get_task_access
from data_access.tasks.get_task_status import get_task_status
from data_access.tasks.update_task import update_task as update_task_row

from .exceptions import InvalidTaskInput


class TaskNotVisible(Exception):
    """No such task, or the caller may not see that it exists."""


class TaskUpdateNotPermitted(Exception):
    """The authenticated caller is not allowed to make this change."""


DETAIL_FIELDS = {
    "title",
    "description",
    "task_type_id",
    "priority_id",
    "start_date",
    "due_date",
    "estimated_hours",
}

FULL_EDIT_ROLES = {"admin", "manager"}
REASSIGN_ROLES = {"admin"}


def update_task_details(*, actor, task_id, changes):
    """Validate and apply one partial task update."""
    access = get_task_access(task_id, actor["user_id"])

    if access is None:
        raise TaskNotVisible()

    current_rows = get_project_tasks(
        project_id=access["project_id"],
        task_id=task_id,
    )

    if not current_rows:
        raise TaskNotVisible()

    current = current_rows[0]

    target_status = _target_status(changes)
    _authorise(actor=actor, current=current, changes=changes, target_status=target_status)
    _validate_lookups(current=current, changes=changes)
    _validate_assignee(
        project_id=access["project_id"],
        project_organisation_id=access["organisation_id"],
        changes=changes,
    )
    _validate_effective_dates(current=current, changes=changes)

    with transaction.atomic():
        update_task_row(
            task_id=task_id,
            organisation_id=access["organisation_id"],
            changed_by=actor["user_id"],
            changes=changes,
        )

    updated = get_project_tasks(
        project_id=access["project_id"],
        task_id=task_id,
    )

    if not updated:
        raise TaskNotVisible()

    return updated[0]


def _target_status(changes):
    if "status_id" not in changes:
        return None

    status = get_task_status(changes["status_id"])

    if status is None:
        raise InvalidTaskInput(
            {"status_id": ["No active status with that id."]}
        )

    return status


def _authorise(*, actor, current, changes, target_status):
    role_name = str(actor.get("role_name") or "").strip().lower()

    if role_name in FULL_EDIT_ROLES:
        if "assignee_id" in changes and role_name not in REASSIGN_ROLES:
            raise TaskUpdateNotPermitted()
        return

    # Standard users may only submit one change: status -> Completed.
    if set(changes) != {"status_id"}:
        raise TaskUpdateNotPermitted()

    assignee_ids = {
        int(person["user_id"])
        for person in current.get("assignees", [])
        if person.get("user_id") is not None
    }

    if actor["user_id"] not in assignee_ids:
        raise TaskUpdateNotPermitted()

    if (
        target_status is None
        or str(target_status["status_name"]).strip().lower() != "completed"
    ):
        raise TaskUpdateNotPermitted()


def _validate_lookups(*, current, changes):
    lookup_fields = {"task_type_id", "status_id", "priority_id"}

    if not lookup_fields.intersection(changes):
        return

    values = {
        "task_type_id": changes.get("task_type_id", current["task_type_id"]),
        "status_id": changes.get("status_id", current["status_id"]),
        "priority_id": changes.get("priority_id", current["priority_id"]),
    }

    known = check_task_lookups(**values)

    flags = {
        "task_type_id": ("task_type_exists", "No active task type with that id."),
        "status_id": ("status_exists", "No active status with that id."),
        "priority_id": ("priority_exists", "No active priority with that id."),
    }

    errors = {}

    for field, (flag, message) in flags.items():
        if field in changes and not known[flag]:
            errors[field] = [message]

    if errors:
        raise InvalidTaskInput(errors)


def _validate_assignee(*, project_id, project_organisation_id, changes):
    if "assignee_id" not in changes:
        return

    access = get_project_user_access(
        project_id=project_id,
        user_id=changes["assignee_id"],
    )

    if access is None or access["user_id"] is None:
        raise InvalidTaskInput(
            {"assignee_id": ["No user with that id."]}
        )

    if access["user_organisation_id"] != project_organisation_id:
        raise InvalidTaskInput(
            {
                "assignee_id": [
                    "That user does not belong to this project's organisation."
                ]
            }
        )

    if not access["is_member"]:
        raise InvalidTaskInput(
            {"assignee_id": ["That user is not a member of this project."]}
        )


def _validate_effective_dates(*, current, changes):
    start_date = changes.get("start_date", current.get("start_date"))
    due_date = changes.get("due_date", current.get("due_date"))

    if start_date and due_date and due_date < start_date:
        raise InvalidTaskInput(
            {"due_date": ["Due date cannot be before the start date."]}
        )
