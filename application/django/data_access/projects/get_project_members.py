"""Read project membership through the project-members stored procedure."""

from ._procedure import call_procedure

PROCEDURE_NAME = "sp_get_project_members"


def get_project_members(*, project_id, organisation_id):
    return call_procedure(
        PROCEDURE_NAME,
        [project_id, organisation_id],
    )
