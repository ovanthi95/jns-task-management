# API 05 - Get Projects
# Owner: Jessie

from django.db import connection


def get_projects(organisation_id, user_id=None, can_view_all=True):
    with connection.cursor() as cursor:
        cursor.callproc(
            "sp_get_projects",
            [
                organisation_id,
                user_id,
                1 if can_view_all else 0,
            ]
        )

        rows = cursor.fetchall()
        if not rows:
            return []

        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in rows]
