"""Read project membership through the project-members stored procedure."""

from django.db import connection


def get_project_members(*, project_id, organisation_id):
    with connection.cursor() as cursor:
        cursor.callproc(
            "sp_get_project_members",
            [project_id, organisation_id],
        )
        rows = cursor.fetchall()

        if not rows:
            return []

        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in rows]
