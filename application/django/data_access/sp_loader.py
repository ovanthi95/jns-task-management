# Shared stored-procedure loader for MySQL integration tests
# Owner: Manatka (assigned in playbook section 9.4 / 16)
#
# Django builds the temporary test database from migrations only, so stored
# procedures do not exist there. Tests call load_stored_procedures() in
# setUpClass to load the .sql files they need from data/stored_procedures/.
#
# The .sql files use the mysql-client DELIMITER convention. The server does not
# understand DELIMITER, so this loader strips those lines and splits on the
# "$$" delimiter before executing each statement through the Django connection.
#
# Usage in a test module:
#
#     from data_access.sp_loader import load_stored_procedures
#
#     @classmethod
#     def setUpClass(cls):
#         super().setUpClass()
#         load_stored_procedures("users/sp_get_users", "users/sp_get_session_user")
#
# Names are paths relative to data/stored_procedures/, without the .sql suffix.

from pathlib import Path

from django.db import connection

# application/django/data_access/sp_loader.py -> repo root is four levels up
REPO_ROOT = Path(__file__).resolve().parents[3]
STORED_PROCEDURES_DIR = REPO_ROOT / "data" / "stored_procedures"

DELIMITER_TOKEN = "$$"


def _statements_from_sql(sql_text):
    """Return executable statements from mysql-client DELIMITER files.

    The merged repository contains both `DELIMITER $` and `DELIMITER $$`
    procedure files. DELIMITER is a mysql command-line directive, not SQL, so
    it must be interpreted here rather than sent to the server.

    Parsing line-by-line also avoids splitting on ordinary semicolons inside a
    CREATE PROCEDURE body.
    """

    delimiter = ";"
    buffer = []
    statements = []

    def flush():
        text = "\n".join(buffer).strip()

        if text:
            statements.append(text)

        buffer.clear()

    for raw_line in sql_text.splitlines():
        stripped = raw_line.strip()

        if stripped.upper().startswith("DELIMITER "):
            if buffer:
                flush()

            delimiter = stripped.split(None, 1)[1]
            continue

        if not stripped or stripped.startswith("--"):
            continue

        buffer.append(raw_line)

        text = "\n".join(buffer).rstrip()

        if delimiter and text.endswith(delimiter):
            text = text[: -len(delimiter)].rstrip()

            if text:
                statements.append(text)

            buffer.clear()

    if buffer:
        flush()

    return statements

def load_stored_procedures(*names):
    """Load one or more procedure files into the current Django database.

    Each name is relative to data/stored_procedures/ without ".sql", for
    example "users/sp_get_users". Files are executed in the order given.
    Raises FileNotFoundError for a missing file so a typo fails loudly.
    """

    if connection.vendor != "mysql":
        raise RuntimeError(
            "Stored procedures require MySQL. Set DB_ENGINE=mysql for this test run."
        )

    for name in names:
        path = STORED_PROCEDURES_DIR / f"{name}.sql"

        if not path.is_file():
            raise FileNotFoundError(f"Stored procedure file not found: {path}")

        sql_text = path.read_text(encoding="utf-8")

        with connection.cursor() as cursor:
            for statement in _statements_from_sql(sql_text):
                cursor.execute(statement)