"""API 12 user update persistence."""

from django.db import connection


def update_user(*, user_id, organisation_id, changes):
    values = [
        user_id,
        organisation_id,
        int("first_name" in changes),
        changes.get("first_name"),
        int("last_name" in changes),
        changes.get("last_name"),
        int("email" in changes),
        changes.get("email"),
        int("role_id" in changes),
        changes.get("role_id"),
        int("availability" in changes),
        changes.get("availability"),
        int("status" in changes),
        changes.get("status"),
    ]

    with connection.cursor() as cursor:
        cursor.callproc("sp_update_user", values)
        row = cursor.fetchone()

        if row is None:
            return None

        columns = [column[0] for column in cursor.description]
        return dict(zip(columns, row))
