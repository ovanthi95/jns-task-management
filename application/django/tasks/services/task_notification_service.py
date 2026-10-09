"""Email notifications for task assignments."""

from django.conf import settings
from django.core.mail import EmailMessage

from tasks.models import Task, TaskAssignee


def send_task_assignment_email(*, task_id, assigned_by_name):
    task = (
        Task.objects
        .select_related("project", "priority")
        .filter(task_id=task_id)
        .first()
    )
    if task is None:
        return False

    assignment = (
        TaskAssignee.objects
        .select_related("user")
        .filter(task_id=task_id)
        .first()
    )
    if assignment is None or not assignment.user.email:
        return False

    assignee = assignment.user
    description = (
        task.description.strip()
        if task.description
        else "No description provided."
    )

    body = (
        f"Hello {assignee.first_name},\n\n"
        "A new task has been assigned to you in JNS Task Management.\n\n"
        f"Project: {task.project.project_name}\n"
        f"Task: {task.title}\n"
        f"Description: {description}\n"
        f"Priority: {task.priority.priority_name}\n"
        f"Start date: {task.start_date or 'Not specified'}\n"
        f"Due date: {task.due_date or 'Not specified'}\n"
        f"Estimated hours: {task.estimated_hours or 'Not specified'}\n\n"
        f"Assigned by: {assigned_by_name}\n\n"
        "Please sign in to JNS Task Management to view and manage the task."
    )

    message = EmailMessage(
        subject=f"New task assigned: {task.title}",
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[assignee.email],
    )

    return message.send(fail_silently=False) > 0


def send_task_update_email(*, task_id, updated_by_id, changes):
    """Send the selected task changes to its current assignee."""
    task = (
        Task.objects
        .select_related("project", "priority", "status", "task_type")
        .filter(task_id=task_id)
        .first()
    )
    if task is None:
        return False

    assignment = (
        TaskAssignee.objects
        .select_related("user")
        .filter(task_id=task_id)
        .first()
    )
    if assignment is None or not assignment.user.email:
        return False

    updated_by = Task.objects.none()
    from users.models import User
    actor = User.objects.filter(user_id=updated_by_id).first()

    assignee = assignment.user
    labels = {
        "title": "Title",
        "description": "Description",
        "task_type_id": "Task type",
        "priority_id": "Priority",
        "assignee_id": "Assignee",
        "start_date": "Start date",
        "due_date": "Due date",
        "estimated_hours": "Estimated hours",
        "status_id": "Status",
    }

    def display(value):
        if isinstance(value, dict):
            value = (
                value.get("name")
                or value.get("priority_name")
                or value.get("status_name")
                or value.get("type_name")
            )
        return "Not specified" if value is None or value == "" else str(value)

    change_lines = []
    for field, (old_value, new_value) in changes.items():
        change_lines.append(
            f"{labels.get(field, field.replace('_', ' ').capitalize())}: "
            f"{display(old_value)} -> {display(new_value)}"
        )

    description = (
        task.description.strip()
        if task.description
        else "No description provided."
    )

    body = (
        f"Hello {assignee.first_name},\n\n"
        "A task assigned to you has been updated in JNS Business Solutions "
        "Worklink.\n\n"
        "Changes:\n"
        + "\n".join(change_lines)
        + "\n\nCurrent task details:\n"
        f"Project: {task.project.project_name}\n"
        f"Task: {task.title}\n"
        f"Description: {description}\n"
        f"Task type: {task.other_task_type or task.task_type.type_name}\n"
        f"Priority: {task.priority.priority_name}\n"
        f"Status: {task.status.status_name}\n"
        f"Start date: {task.start_date or 'Not specified'}\n"
        f"Due date: {task.due_date or 'Not specified'}\n"
        f"Estimated hours: {task.estimated_hours or 'Not specified'}\n\n"
        f"Updated by: {((actor.first_name + ' ' + actor.last_name).strip() if actor else 'Worklink administrator')}\n"
    )

    message = EmailMessage(
        subject=f"Task updated: {task.title}",
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[assignee.email],
    )

    return message.send(fail_silently=False) > 0
