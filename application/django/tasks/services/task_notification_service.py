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
