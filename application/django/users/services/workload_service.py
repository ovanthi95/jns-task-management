"""Application logic for workload reporting."""

from data_access.users.get_workload import (
    get_user_workload,
    get_user_workload_tasks,
    get_workload,
)
from users.services.permission_service import actor_has_permission


def list_workload(*, actor):
    if actor_has_permission(actor, "view_all_tasks"):
        rows = get_workload(actor["organisation_id"])
    else:
        rows = get_user_workload(
            actor["organisation_id"],
            actor["user_id"],
        )

    for row in rows:
        projects = row.pop("current_projects", None)
        row["current_projects"] = (
            [item for item in projects.split("||") if item]
            if projects
            else []
        )

    return rows


def list_user_workload_tasks(*, actor, user_id):
    if (
        int(user_id) != int(actor["user_id"])
        and not actor_has_permission(actor, "view_all_tasks")
    ):
        return None

    return get_user_workload_tasks(
        actor["organisation_id"],
        user_id,
    )
