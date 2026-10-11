"""Persist project membership through the project-members stored procedure."""

import json

from ._procedure import call_procedure

PROCEDURE_NAME = "sp_update_project_members"


def update_project_members(*, project_id, organisation_id, member_ids):
    return call_procedure(
        PROCEDURE_NAME,
        [
            project_id,
            organisation_id,
            json.dumps([int(member_id) for member_id in member_ids]),
        ],
    )
