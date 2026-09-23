# API 02 - Users list
# Owner: Manatka
# Calls sp_get_users

from django.db import connection


def get_users(organisation_id):
    """All users in one organisation, as a list of dicts. One SP call, no logic."""

    with connection.cursor() as cursor:
        cursor.callproc("sp_get_users", [organisation_id])

        rows = cursor.fetchall()

        if not rows:
            return []

        columns = [column[0] for column in cursor.description]

        return [dict(zip(columns, row)) for row in rows]