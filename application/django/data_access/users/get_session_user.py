from django.db import connection


def get_session_user(user_id):
    with connection.cursor() as cursor:
        cursor.callproc("sp_get_session_user", [user_id])

        row = cursor.fetchone()

        if row is None:
            return None

        columns = [column[0] for column in cursor.description]

        return dict(zip(columns, row))