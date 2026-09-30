# API 06 task creation application logic
# Owner: Edward

"""API 06 task creation application logic."""

from django.db import transaction

from data_access.tasks.check_task_lookups import check_task_lookups
from data_access.tasks.create_task import create_task as create_task_row
from data_access.tasks.get_project_tasks import get_project_tasks
from data_access.tasks.get_project_user_access import get_project_user_access

from users.services.permission_service import actor_has_permission

from .exceptions import InvalidTaskInput, RoleNotPermitted
from .project_access import require_visible_project

LOOKUP_FIELDS = (
    ("task_type_id", "task_type_exists", "No task type with that id."),
    ("status_id", "status_exists", "No status with that id."),
    ("priority_id", "priority_exists", "No priority with that id."),
)


def user_may_create_task(user):
    return actor_has_permission(user, "create_tasks")


def create_task(*, project_id, user, data):
    if not user_may_create_task(user):
        raise RoleNotPermitted()

    project = require_visible_project(project_id=project_id, user=user)

    if (project.get("project_status") or "").lower() != "active":
        raise InvalidTaskInput({
            "detail": ["Tasks can only be added to an Active project."]
        })

    _require_known_lookups(data)
    _require_eligible_assignee(
        project=project,
        assignee_id=data["assignee_id"],
    )

    with transaction.atomic():
        task_id = create_task_row(
            project_id=project_id,
            task_type_id=data["task_type_id"],
            status_id=data["status_id"],
            priority_id=data["priority_id"],
            title=data["title"],
            description=data.get("description"),
            start_date=data.get("start_date"),
            due_date=data.get("due_date"),
            estimated_hours=data.get("estimated_hours"),
            assignee_user_id=data["assignee_id"],
            created_by=user["user_id"],
        )

    return get_project_tasks(
        project_id=project_id,
        task_id=task_id,
    )[0]


def _require_known_lookups(data):
    known = check_task_lookups(
        task_type_id=data["task_type_id"],
        status_id=data["status_id"],
        priority_id=data["priority_id"],
    )

    errors = {
        field: [message]
        for field, flag, message in LOOKUP_FIELDS
        if not known[flag]
    }

    if errors:
        raise InvalidTaskInput(errors)


def _require_eligible_assignee(*, project, assignee_id):
    access = get_project_user_access(
        project_id=project["project_id"],
        user_id=assignee_id,
    )

    if access is None or access["user_id"] is None:
        raise InvalidTaskInput(
            {"assignee_id": ["No user with that id."]}
        )

    if access["user_organisation_id"] != project["project_organisation_id"]:
        raise InvalidTaskInput({
            "assignee_id": [
                "That user does not belong to this project's organisation."
            ]
        })

    if not access["is_member"]:
        raise InvalidTaskInput(
            {"assignee_id": ["That user is not a member of this project."]}
        )
