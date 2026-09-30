"""Task discussion application logic."""

from data_access.tasks.add_comment import add_comment
from data_access.tasks.get_task_access import get_task_access
from data_access.tasks.get_task_comments import get_task_comments


class CommentTaskNotFound(Exception):
    pass


def _require_access(*, actor_user_id, task_id):
    access = get_task_access(task_id, actor_user_id)

    if access is None:
        raise CommentTaskNotFound()

    return access


def list_task_comments(*, actor_user_id, task_id):
    _require_access(actor_user_id=actor_user_id, task_id=task_id)
    return get_task_comments(task_id)


def create_task_comment(*, actor_user_id, task_id, comment_text):
    _require_access(actor_user_id=actor_user_id, task_id=task_id)

    return add_comment(
        task_id=task_id,
        user_id=actor_user_id,
        comment_text=comment_text.strip(),
    )
