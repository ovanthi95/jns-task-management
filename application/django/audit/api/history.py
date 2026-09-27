"""API 13 - central Project, Task and User history."""

from datetime import datetime, time

from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from audit.models import AuditLog
from projects.models import Project
from tasks.models import Task, TaskHistory
from users.models import User
from users.services.permission_service import actor_has_permission
from users.services.session_service import get_authenticated_session_user

VALID_TYPES = {"Project", "Task", "User"}


def _day_boundary(value, end=False):
    if not value:
        return None
    try:
        day = datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None
    dt = datetime.combine(day, time.max if end else time.min)
    return timezone.make_aware(dt) if timezone.is_naive(dt) else dt


def _matches(row, search_text):
    tokens = [part for part in search_text.lower().split() if part]
    if not tokens:
        return True

    haystack = " ".join([
        str(row.get("entity_name") or ""),
        str(row.get("description") or ""),
        str(row.get("field_name") or ""),
        str(row.get("old_value") or ""),
        str(row.get("new_value") or ""),
        str(row.get("changed_by_name") or ""),
    ]).lower()

    return all(token in haystack for token in tokens)


def _current_projects(organisation_id, search_text):
    rows = (
        Project.objects
        .filter(organisation_id=organisation_id, status="Active")
        .annotate(
            total_tasks=Count("tasks", distinct=True),
            completed_tasks=Count(
                "tasks",
                filter=Q(tasks__status__status_name="Completed"),
                distinct=True,
            ),
        )
        .order_by("project_name", "project_id")
    )

    if search_text:
        rows = rows.filter(
            Q(project_name__icontains=search_text)
            | Q(description__icontains=search_text)
        )

    return [
        {
            "entity_id": item.project_id,
            "entity_name": item.project_name,
            "status": item.status,
            "start_date": item.start_date,
            "end_date": item.end_date,
            "completed_tasks": item.completed_tasks,
            "total_tasks": item.total_tasks,
        }
        for item in rows
    ]


def _current_tasks(organisation_id, search_text):
    rows = (
        Task.objects
        .filter(
            project__organisation_id=organisation_id,
            project__status="Active",
        )
        .exclude(status__status_name="Completed")
        .select_related("project", "status", "priority")
        .prefetch_related("assignees__user")
        .order_by("due_date", "title", "task_id")
    )

    if search_text:
        rows = rows.filter(
            Q(title__icontains=search_text)
            | Q(description__icontains=search_text)
            | Q(project__project_name__icontains=search_text)
            | Q(assignees__user__first_name__icontains=search_text)
            | Q(assignees__user__last_name__icontains=search_text)
        ).distinct()

    return [
        {
            "entity_id": task.task_id,
            "entity_name": task.title,
            "project_id": task.project_id,
            "project_name": task.project.project_name,
            "status": task.status.status_name,
            "priority": task.priority.priority_name,
            "due_date": task.due_date,
            "assignees": [
                {
                    "user_id": assignment.user.user_id,
                    "name": f"{assignment.user.first_name} {assignment.user.last_name}".strip(),
                }
                for assignment in task.assignees.all()
            ],
        }
        for task in rows
    ]


def _audit_rows(actor_data, entity_type, changed_by, start_date, end_date):
    queryset = (
        AuditLog.objects
        .filter(
            organisation_id=actor_data["organisation_id"],
            entity_type=entity_type,
        )
        .select_related("user")
        .order_by("-created_at", "-audit_log_id")
    )

    if changed_by:
        queryset = queryset.filter(user_id=changed_by)
    if start_date:
        queryset = queryset.filter(created_at__gte=start_date)
    if end_date:
        queryset = queryset.filter(created_at__lte=end_date)

    result = []
    for item in queryset[:1000]:
        result.append({
            "history_id": f"audit-{item.audit_log_id}",
            "entity_type": item.entity_type,
            "entity_id": item.entity_id,
            "entity_name": item.entity_name,
            "action": item.action,
            "field_name": item.field_name,
            "description": item.description,
            "old_value": item.old_value,
            "new_value": item.new_value,
            "changed_by_id": item.user_id,
            "changed_by_name": (
                f"{item.user.first_name} {item.user.last_name}".strip()
                if item.user else "System"
            ),
            "created_at": item.created_at,
        })
    return result


def _task_history_rows(actor_data, changed_by, start_date, end_date):
    queryset = (
        TaskHistory.objects
        .filter(task__project__organisation_id=actor_data["organisation_id"])
        .select_related("task", "task__project", "changed_by")
        .order_by("-changed_at", "-history_id")
    )

    if changed_by:
        queryset = queryset.filter(changed_by_id=changed_by)
    if start_date:
        queryset = queryset.filter(changed_at__gte=start_date)
    if end_date:
        queryset = queryset.filter(changed_at__lte=end_date)

    return [
        {
            "history_id": f"task-{item.history_id}",
            "entity_type": "Task",
            "entity_id": item.task_id,
            "entity_name": item.task.title,
            "action": "Updated",
            "field_name": item.field_name,
            "description": f"Project: {item.task.project.project_name}",
            "old_value": item.old_value,
            "new_value": item.new_value,
            "changed_by_id": item.changed_by_id,
            "changed_by_name": (
                f"{item.changed_by.first_name} {item.changed_by.last_name}".strip()
            ),
            "created_at": item.changed_at,
        }
        for item in queryset[:1000]
    ]


class HistoryView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        actor = get_authenticated_session_user(request.session.get("user_id"))

        if actor is None:
            request.session.flush()
            return Response(
                {"detail": "Not authenticated."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not actor_has_permission(actor, "view_history"):
            return Response(
                {"detail": "History permission required."},
                status=status.HTTP_403_FORBIDDEN,
            )

        entity_type = request.query_params.get("entity_type", "Project")
        if entity_type not in VALID_TYPES:
            return Response(
                {"entity_type": ["Choose Project, Task, or User."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        changed_by_raw = request.query_params.get("changed_by")
        changed_by = None
        if changed_by_raw:
            try:
                changed_by = int(changed_by_raw)
            except ValueError:
                return Response(
                    {"changed_by": ["Choose a valid user."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        search_text = request.query_params.get("search", "").strip()
        start_date = _day_boundary(request.query_params.get("from"))
        end_date = _day_boundary(request.query_params.get("to"), end=True)

        rows = _audit_rows(
            actor,
            entity_type,
            changed_by,
            start_date,
            end_date,
        )

        if entity_type == "Task":
            rows.extend(
                _task_history_rows(
                    actor,
                    changed_by,
                    start_date,
                    end_date,
                )
            )

        rows = [row for row in rows if _matches(row, search_text)]
        rows.sort(key=lambda row: row["created_at"], reverse=True)

        current_items = (
            _current_projects(actor["organisation_id"], search_text)
            if entity_type == "Project"
            else _current_tasks(actor["organisation_id"], search_text)
            if entity_type == "Task"
            else []
        )

        changers = (
            User.objects
            .filter(organisation_id=actor["organisation_id"])
            .filter(
                Q(audit_logs__isnull=False)
                | Q(task_history_entries__isnull=False)
            )
            .distinct()
            .order_by("first_name", "last_name")
        )

        return Response({
            "items": rows[:1000],
            "total": min(len(rows), 1000),
            "current_items": current_items,
            "current_total": len(current_items),
            "changed_by_options": [
                {
                    "user_id": user.user_id,
                    "name": f"{user.first_name} {user.last_name}".strip(),
                }
                for user in changers
            ],
        })
