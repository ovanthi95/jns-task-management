"""Persist project membership through the project-members stored procedure."""

import json

from django.db import connection


def update_project_members(*, project_id, organisation_id, member_ids):
    with connection.cursor() as cursor:
        cursor.callproc(
            "sp_update_project_members",
            [
                project_id,
                organisation_id,
                json.dumps([int(member_id) for member_id in member_ids]),
            ],
        )

        rows = cursor.fetchall()
        if not rows:
            return []

        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in rows]
