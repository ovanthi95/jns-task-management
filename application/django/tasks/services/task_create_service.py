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
    """The role rule on its own, so the endpoint can answer it before parsing.

    The rule lives here rather than in the endpoint so there is one definition
    of it. create_task applies it again, which means the rule still holds if
    this service is ever called from somewhere that has no HTTP layer in front
    of it.
    """
    role = getattr(user, "role", None)

    return role is not None and role.role_name.lower() in TASK_CREATOR_ROLES


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
            created_by=user.user_id,
        )

    # Read back rather than assemble the response by hand: created_at and the
    # lookup names are the database's answer, not this module's guess, and
    # using API 07's query keeps the two response shapes identical.
    return get_project_tasks(project_id=project_id, task_id=task_id)[0]


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
