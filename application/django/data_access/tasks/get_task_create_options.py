"""Read-only support data for the API 06 create-task form."""

from ._procedure import call_procedure

PROCEDURE_NAME = "sp_get_task_create_options"


def get_task_create_options(project_id):
    rows = call_procedure(PROCEDURE_NAME, [project_id])

    result = {
        "project": None,
        "task_types": [],
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
        elif group == "priority":
            result["priorities"].append({
                "priority_id": row["option_id"],
                "priority_name": row["option_name"],
            })
        elif group == "new_status":
            result["new_status_id"] = row["option_id"]
        elif group == "user":
            result["users"].append({
                "user_id": row["option_id"],
                "name": row["option_name"],
                "role_name": row["extra_name"],
            })

    return result
