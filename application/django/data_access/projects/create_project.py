# API 04 - Create Project
# Owner: Jessie
# Calls sp_create_project

import json

from django.db import connection


def create_project(
    organisation_id,
    project_name,
    description,
    start_date,
    end_date,
    created_by,
    member_ids
):
    with connection.cursor() as cursor:
        cursor.callproc(
            "sp_create_project",
            [
                organisation_id,
                project_name,
                description,
                start_date,
                end_date,
                created_by,
                json.dumps(member_ids)
            ]
        )

        row = cursor.fetchone()

        if row is None:
            return None

        columns = [column[0] for column in cursor.description]

        return dict(zip(columns, row))