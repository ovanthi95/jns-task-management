"""API 07 - Task list application logic

Owner: Edward
Application/business logic belongs here.
This service may call one or more data-access functions.

API 07 is open to any member of the project, including roles that cannot
create a task. Being allowed to see a project's work and being allowed to add
to it are two different rules.

Nothing in this module reads a table through the ORM. Every database call
goes through data_access, and every data_access function calls exactly one
stored procedure.
"""

from data_access.tasks.get_project_tasks import get_project_tasks

from .project_access import require_visible_project


def list_project_tasks(
    *,
    project_id,
    user,
    status_id=None,
    priority_id=None,
    assignee_id=None,
):
    """Return this project's tasks, newest first, in the read shape.

    The three filters are optional and AND together: supplying more than one
    narrows the result rather than widening it.

    A filter id that is a valid integer but matches no row is not an error. It
    simply selects nothing and the caller gets an empty list. Rejecting a
    filter value that is not a number at all is the endpoint's job, because
    that is a parsing question, not a business rule.

    Ordering is fixed rather than client-controlled, so the same request twice
    gives the same order: newest first, with the task id breaking ties between
    rows created in the same instant.
    """
    require_visible_project(project_id=project_id, user=user)

    return get_project_tasks(
        project_id=project_id,
        status_id=status_id,
        priority_id=priority_id,
        assignee_id=assignee_id,
    )
