# API 10 - Add file metadata
# Owner: Manatka
# Calls sp_add_file

from django.db import connection


def add_file(task_id, uploaded_by, file_name, file_type, file_size, s3_key):
    """Insert one attachments row and return it as a dict. One SP call, no logic."""

    with connection.cursor() as cursor:
        cursor.callproc(
            "sp_add_file",
            [task_id, uploaded_by, file_name, file_type, file_size, s3_key],
        )

        row = cursor.fetchone()

        if row is None:
            return None

        columns = [column[0] for column in cursor.description]

        return dict(zip(columns, row))