"""Email notifications for task assignments and updates."""

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
        "A new task has been assigned to you in JNS Business Solutions.\n\n"
        f"Project: {task.project.project_name}\n"
        f"Task: {task.title}\n"
        f"Description: {description}\n"
        f"Priority: {task.priority.priority_name}\n"
        f"Start date: {task.start_date or 'Not specified'}\n"
        f"Due date: {task.due_date or 'Not specified'}\n"
        f"Estimated hours: {task.estimated_hours or 'Not specified'}\n\n"
        f"Assigned by: {assigned_by_name}\n"
    )

    message = EmailMessage(
        subject=f"New task assigned: {task.title}",
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[assignee.email],
    )

    return message.send(fail_silently=False) > 0


def send_task_update_email(*, task, assigned_by_name, changes):
    """Email the current assignee about actual task changes."""
    assignees = task.get("assignees") or []
    if not assignees:
        return False

    assignee_id = assignees[0].get("user_id")
    if not assignee_id:
        return False

    assignment = (
        TaskAssignee.objects
        .select_related("user")
        .filter(task_id=task["task_id"], user_id=assignee_id)
        .first()
    )
    if assignment is None or not assignment.user.email:
        return False

    recipient = assignment.user

    labels = {
        "task_type_id": "Task type",
        "priority_id": "Priority",
        "assignee_id": "Assignee",
        "status_id": "Status",
        "title": "Title",
        "description": "Description",
        "start_date": "Start date",
        "due_date": "Due date",
        "estimated_hours": "Estimated hours",
    }

    def display(value):
        if value is None or value == "":
            return "Not specified"
        return str(value)

    changed_lines = "\n".join(
        f"{labels.get(field, field.replace('_', ' ').capitalize())}: "
        f"{display(old)} → {display(new)}"
        for field, (old, new) in changes.items()
    )

    task_row = (
        Task.objects
        .select_related("project", "priority", "status", "task_type")
        .filter(task_id=task["task_id"])
        .first()
    )
    if task_row is None:
        return False

    description = (
        task_row.description.strip()
        if task_row.description
        else "No description provided."
    )

    body = (
        f"Hello {recipient.first_name},\n\n"
        "A task assigned to you has been updated in JNS Business Solutions.\n\n"
        "Changes:\n"
        f"{changed_lines}\n\n"
        "Current task details:\n"
        f"Project: {task_row.project.project_name}\n"
        f"Task: {task_row.title}\n"
        f"Description: {description}\n"
        f"Priority: {task_row.priority.priority_name}\n"
        f"Status: {task_row.status.status_name}\n"
        f"Start date: {task_row.start_date or 'Not specified'}\n"
        f"Due date: {task_row.due_date or 'Not specified'}\n"
        f"Estimated hours: {task_row.estimated_hours or 'Not specified'}\n\n"
        f"Updated by: {assigned_by_name}\n"
    )

    message = EmailMessage(
        subject=f"Task updated: {task_row.title}",
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient.email],
    )

    return message.send(fail_silently=False) > 0
