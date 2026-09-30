"""API 09 comment persistence."""

from ._procedure import call_procedure

PROCEDURE_NAME = "sp_add_comment"


def add_comment(*, task_id, user_id, comment_text):
    rows = call_procedure(
        PROCEDURE_NAME,
        [task_id, user_id, comment_text],
    )

    return rows[0] if rows else None
