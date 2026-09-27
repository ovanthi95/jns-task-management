"""Persistence for workload reporting."""

from django.db import connection


def get_workload(organisation_id):
    with connection.cursor() as cursor:
        cursor.callproc("sp_get_workload", [organisation_id])
        rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in rows]


def get_user_workload_tasks(organisation_id, user_id):
    with connection.cursor() as cursor:
        cursor.callproc(
            "sp_get_user_workload_tasks",
            [organisation_id, user_id],
        )
        rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in rows]
