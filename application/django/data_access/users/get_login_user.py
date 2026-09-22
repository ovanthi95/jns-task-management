# API 01 - Login
# Owner: Ovanthi
# Calls sp_get_login_user

from django.db import connection


def get_login_user(email):
    with connection.cursor() as cursor:
        cursor.callproc("sp_get_login_user", [email])

        row = cursor.fetchone()

        if row is None:
            return None

        columns = [column[0] for column in cursor.description]

        return dict(zip(columns, row))