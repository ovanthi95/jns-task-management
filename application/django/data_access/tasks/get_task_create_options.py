"""Read-only support data for task creation and list filters."""

from ._procedure import call_procedure

PROCEDURE_NAME = "sp_get_task_create_options"


def get_task_create_options(project_id):
    rows = call_procedure(PROCEDURE_NAME, [project_id])

    result = {
        "project": None,
        "task_types": [],
        "task_statuses": [],
        "priorities": [],
        "users": [],
        "new_status_id": None,
    }

    for row in rows:
        group = row["option_group"]

        if group == "project":
            result["project"] = {
                "project_id": row["option_id"],
                "project_name": row["option_name"],
                "status": row["extra_name"],
            }
        elif group == "task_type":
            result["task_types"].append({
                "task_type_id": row["option_id"],
                "type_name": row["option_name"],
            })
        elif group == "task_status":
            item = {
                "status_id": row["option_id"],
                "status_name": row["option_name"],
            }
            result["task_statuses"].append(item)

            if (row["option_name"] or "").lower() == "new":
                result["new_status_id"] = row["option_id"]
        elif group == "priority":
            result["priorities"].append({
                "priority_id": row["option_id"],
                "priority_name": row["option_name"],
            })
        elif group == "user":
            result["users"].append({
                "user_id": row["option_id"],
                "name": row["option_name"],
                "role_name": row["extra_name"],
            })

    return result
