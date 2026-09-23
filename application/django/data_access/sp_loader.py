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
    """Split a DELIMITER $$ style file into executable statements.

    Split on "$$" FIRST. The "DELIMITER $$" line itself contains the token, so
    the CREATE PROCEDURE body lands in its own chunk, separate from the
    DROP statement before it. Only then are the DELIMITER lines discarded.

    Outside a procedure body, "--" comment lines are dropped before splitting
    on ";" so a semicolon inside a comment cannot produce a bogus statement.
    Inside CREATE PROCEDURE the server parses comments itself.
    """

    statements = []

    for chunk in sql_text.split(DELIMITER_TOKEN):
        kept_lines = [
            line for line in chunk.splitlines()
            if not line.strip().upper().startswith("DELIMITER")
        ]

        statement = "\n".join(kept_lines).strip()

        if not statement:
            continue

        if statement.upper().startswith("CREATE PROCEDURE"):
            statements.append(statement)
            continue

        code_lines = [
            line for line in kept_lines
            if line.strip() and not line.strip().startswith("--")
        ]

        for part in "\n".join(code_lines).split(";"):
            part = part.strip()

            if part:
                statements.append(part)

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