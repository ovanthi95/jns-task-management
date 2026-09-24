# API 03 - User create
# Owner: Manatka
# Calls sp_create_user

from django.db import connection


def create_user(organisation_id, role_id, first_name, last_name, email,
                password_hash, availability):
    """Insert one user and return the new row as a dict. One SP call, no logic.

    Database errors (duplicate email 1062, unknown role 1452) are raised as
    django.db.IntegrityError and interpreted by the service, not here.
    """

    with connection.cursor() as cursor:
        cursor.callproc(
            "sp_create_user",
            [organisation_id, role_id, first_name, last_name, email,
             password_hash, availability],
        )

        row = cursor.fetchone()

        if row is None:
            return None

        columns = [column[0] for column in cursor.description]

        return dict(zip(columns, row))