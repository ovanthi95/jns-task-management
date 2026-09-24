"""Shared plumbing for the tasks data-access modules.

Owner: Edward

This module holds no business logic and calls no stored procedure of its own.
It exists so that create_task.py, get_project_tasks.py and
get_project_user_access.py do not each repeat the same cursor handling.

Private by convention (leading underscore): nothing outside
data_access/tasks/ should import it.
"""

from django.db import connection


def call_procedure(procedure_name, params):
    """Call one stored procedure and return its first result set.

    Returns a list of dicts, one per row, keyed by the column names the
    procedure selected. Returns an empty list when the procedure produced no
    result set.

    The connection is Django's, so a procedure called inside
    transaction.atomic() takes part in that transaction.
    """
    with connection.cursor() as cursor:
        cursor.callproc(procedure_name, params)
        rows = _rows_as_dicts(cursor)

        # A CALL leaves the procedure's closing status packet queued behind
        # the result set. Draining it here keeps the connection usable; the
        # next statement would otherwise fail with "Commands out of sync".
        while cursor.nextset():
            pass

    return rows


def _rows_as_dicts(cursor):
    if cursor.description is None:
        return []

    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]
