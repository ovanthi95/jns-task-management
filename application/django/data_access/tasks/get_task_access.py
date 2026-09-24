# API 10 - Task access check
# Owner: Manatka
# Calls sp_get_task_access

from django.db import connection


def get_task_access(task_id, user_id):
    """The task as a dict if this user may work on it, else None. One SP call."""

    with connection.cursor() as cursor:
        cursor.callproc("sp_get_task_access", [task_id, user_id])

        row = cursor.fetchone()

        if row is None:
            return None

        columns = [column[0] for column in cursor.description]

        return dict(zip(columns, row))