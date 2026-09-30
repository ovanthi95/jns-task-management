"""Persistence for project updates."""

from django.db import connection


def update_project(*, project_id, organisation_id, changes):
    def supplied(field):
        return 1 if field in changes else 0

    with connection.cursor() as cursor:
        cursor.callproc("sp_update_project", [
            project_id,
            organisation_id,
            supplied("project_name"),
            changes.get("project_name"),
            supplied("description"),
            changes.get("description"),
            supplied("start_date"),
            changes.get("start_date"),
            supplied("end_date"),
            changes.get("end_date"),
            supplied("status"),
            changes.get("status"),
        ])
        row = cursor.fetchone()
        columns = [column[0] for column in cursor.description]
        return dict(zip(columns, row))
