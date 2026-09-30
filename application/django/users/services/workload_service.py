"""Application logic for workload reporting."""

from data_access.users.get_workload import (
    get_user_workload_tasks,
    get_workload,
)


def list_workload(*, actor):
    rows = get_workload(actor["organisation_id"])

    for row in rows:
        projects = row.pop("current_projects", None)
        row["current_projects"] = (
            [item for item in projects.split("||") if item]
            if projects
            else []
        )

    return rows


def list_user_workload_tasks(*, actor, user_id):
    return get_user_workload_tasks(
        actor["organisation_id"],
        user_id,
    )
