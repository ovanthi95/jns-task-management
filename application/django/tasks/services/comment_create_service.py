"""API 09 comment creation application logic."""

from data_access.tasks.add_comment import add_comment
from data_access.tasks.get_task_access import get_task_access


class CommentTaskNotFound(Exception):
    """No such task, or the caller may not see that it exists."""


def create_task_comment(*, actor_user_id, task_id, comment_text):
    access = get_task_access(task_id, actor_user_id)

    if access is None:
        raise CommentTaskNotFound()

    return add_comment(
        task_id=task_id,
        user_id=actor_user_id,
        comment_text=comment_text,
    )
