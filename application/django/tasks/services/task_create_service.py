"""API 06 - Task creation application logic

Owner: Edward
Application/business logic belongs here.
This service may call one or more data-access functions.

Order of checks, and why it is that order:

  1. role        - a property of the caller alone, so it can be answered
                   without touching the project. Answered first so that a
                   caller who is not allowed to create anything never learns
                   whether the project or the body were acceptable.
  2. project     - organisation plus membership, answered as 404.
  3. lookups     - task_type_id, status_id, priority_id must exist.
  4. assignee    - must be a real user, in the project's organisation, and a
                   member of the project.
  5. write       - task row and assignment row, in one transaction.
  6. read back   - through the same query API 07 uses.

Nothing in this module reads or writes a table through the ORM. Every
database call goes through data_access, and every data_access function calls
exactly one stored procedure.
"""

from django.db import transaction

from audit.services.history_recording import record_history
from data_access.tasks.check_task_lookups import check_task_lookups
from data_access.tasks.create_task import create_task as create_task_row
from data_access.tasks.get_project_tasks import get_project_tasks
from data_access.tasks.get_project_user_access import get_project_user_access

from .exceptions import InvalidTaskInput, RoleNotPermitted
from .project_access import require_visible_project

# Matched case-insensitively against roles.role_name, whose seeded values are
# Admin, Manager, Employee, Intern and Volunteer
# (users/management/commands/seed_lookups.py).
TASK_CREATOR_ROLES = frozenset({"admin", "manager"})

LOOKUP_FIELDS = (
    ("task_type_id", "task_type_exists", "No task type with that id."),
    ("status_id", "status_exists", "No status with that id."),
    ("priority_id", "priority_exists", "No priority with that id."),
)


def user_may_create_task(user):
    """Return whether the caller may create tasks.

    The rule lives here rather than in the endpoint so there is one definition
    of it. create_task applies it again, which means the rule still holds if
    this service is ever called from somewhere that has no HTTP layer in front
    of it.

    `user` is the session dict sp_get_session_user returned, so the role
    arrives already denormalised as role_name and this needs no second query.
    An explicit permission list on the session wins when one is present, so a
    configured RBAC role is honoured; otherwise the seeded role names decide.
    A missing session is not permitted rather than an error, so the endpoint
    can ask the question before it knows whether anyone is logged in.
    """
    if not user:
        return False

    permissions = set(user.get("permissions") or [])

    if permissions:
        return "create_tasks" in permissions

    role_name = user.get("role_name")

    return bool(role_name) and role_name.lower() in TASK_CREATOR_ROLES


def create_task(*, project_id, user, data):
    """Create one task with one assignee and return it in the read shape.

    `data` is already parsed and type-checked by the endpoint's serializer.
    `project_id` comes from the URL and the author comes from the session, so
    neither can be set by the request body.
    """
    if not user_may_create_task(user):
        raise RoleNotPermitted()

    project = require_visible_project(project_id=project_id, user=user)

    _require_known_lookups(data)
    _require_eligible_assignee(project=project, assignee_id=data["assignee_id"])

    # The stored procedure writes two rows. Without this boundary a failure on
    # the second one would leave a task with no assignee behind, which is
    # exactly the state API 06 must never produce.
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

    # Read back through API 07's data shape, then write one central history
    # event without changing the endpoint response contract.
    created = get_project_tasks(project_id=project_id, task_id=task_id)[0]

    assignees = created.get("assignees") or []
    assignee_name = None
    if assignees:
        first = assignees[0]
        assignee_name = (
            f"{first.get('first_name', '')} {first.get('last_name', '')}"
        ).strip()

    record_history(
        organisation_id=project["project_organisation_id"],
        user_id=user["user_id"],
        entity_type="Task",
        entity_id=created["task_id"],
        entity_name=created["title"],
        action="Created",
        new_value={
            "project_id": project_id,
            "status": created.get("status_name"),
            "priority": created.get("priority_name"),
            "task_type": created.get("task_type_name"),
            "assignee": assignee_name,
            "due_date": created.get("due_date"),
        },
        description=f'Created task "{created["title"]}".',
    )

    return created


def _require_known_lookups(data):
    """All three lookup ids, reported together rather than one per request."""

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
    """The assignee has to be someone who can actually work on this project.

    Three separate failures, all reported on the assignee_id field because
    that is the field the client sent:

      * no such user at all;
      * a real user, but in another organisation;
      * a real user in this organisation who is not a member of the project.

    None of these is treated as a 404. The caller has already proved it can
    see this project, so naming the problem with the body it sent gives it
    nothing it did not already have.
    """
    access = get_project_user_access(
        project_id=project["project_id"],
        user_id=assignee_id,
    )

    if access is None or access["user_id"] is None:
        raise InvalidTaskInput(
            {"assignee_id": ["No user with that id."]}
        )

    if access["user_organisation_id"] != project["project_organisation_id"]:
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
