# API 05 - Get Projects
# Owner: Jessie
# Calls sp_get_projects

from django.db import connection


def get_projects(organisation_id):
    with connection.cursor() as cursor:
        cursor.callproc(
            "sp_get_projects",
            [organisation_id]
        )

        rows = cursor.fetchall()

        if not rows:
            return []

        columns = [column[0] for column in cursor.description]

        return [
            dict(zip(columns, row))
            for row in rows
        ]