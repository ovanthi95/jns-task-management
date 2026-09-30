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
from tasks.models import Task
from users.models import User
from users.services.permission_service import actor_has_permission
from users.services.session_service import get_authenticated_session_user


VALID_TYPES = {"Project", "Task", "User"}


def _date_start(value):
    if not value:
        return None
    try:
        day = datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None
    dt = datetime.combine(day, time.min)
    return timezone.make_aware(dt) if timezone.is_naive(dt) else dt


def _date_end(value):
    if not value:
        return None
    try:
        day = datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None
    dt = datetime.combine(day, time.max)
    return timezone.make_aware(dt) if timezone.is_naive(dt) else dt


def _history_search_match(item, search_text):
    tokens = [part for part in search_text.lower().split() if part]
    if not tokens:
        return True

    haystack = " ".join([
        str(item.get("entity_name") or ""),
        str(item.get("description") or ""),
        str(item.get("field_name") or ""),
        str(item.get("old_value") or ""),
        str(item.get("new_value") or ""),
        str(item.get("changed_by_name") or ""),
    ]).lower()

    return all(token in haystack for token in tokens)


def _current_projects(organisation_id, search_text):
    queryset = (
        Project.objects
        .filter(
            organisation_id=organisation_id,
            status="Active",
        )
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
        queryset = queryset.filter(
            Q(project_name__icontains=search_text)
            | Q(description__icontains=search_text)
        )

    return [
        {
            "entity_id": project.project_id,
            "entity_name": project.project_name,
            "status": project.status,
            "start_date": project.start_date,
            "end_date": project.end_date,
            "completed_tasks": project.completed_tasks,
            "total_tasks": project.total_tasks,
        }
        for project in queryset
    ]


def _current_tasks(organisation_id, search_text):
    queryset = (
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
        queryset = queryset.filter(
            Q(title__icontains=search_text)
            | Q(description__icontains=search_text)
            | Q(project__project_name__icontains=search_text)
            | Q(assignees__user__first_name__icontains=search_text)
            | Q(assignees__user__last_name__icontains=search_text)
        ).distinct()

    rows = []
    for task in queryset:
        rows.append({
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
                    "name": (
                        f"{assignment.user.first_name} "
                        f"{assignment.user.last_name}"
                    ).strip(),
                }
                for assignment in task.assignees.all()
            ],
        })

    return rows


class HistoryView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        actor_data = get_authenticated_session_user(
            request.session.get("user_id")
        )

        if actor_data is None:
            request.session.flush()
            return Response(
                {"detail": "Not authenticated."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not actor_has_permission(actor_data, "view_history"):
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

        changed_by = request.query_params.get("changed_by")
        search_text = request.query_params.get("search", "").strip()
        start_date = _date_start(request.query_params.get("from"))
        end_date = _date_end(request.query_params.get("to"))

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
            try:
                queryset = queryset.filter(user_id=int(changed_by))
            except ValueError:
                return Response(
                    {"changed_by": ["Choose a valid user."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)

        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)

        rows = []
        for item in queryset[:1000]:
            changed_by_name = (
                f"{item.user.first_name} {item.user.last_name}".strip()
                if item.user else "System"
            )

            row = {
                "history_id": item.audit_log_id,
                "entity_type": item.entity_type,
                "entity_id": item.entity_id,
                "entity_name": item.entity_name,
                "action": item.action,
                "field_name": item.field_name,
                "description": item.description,
                "old_value": item.old_value,
                "new_value": item.new_value,
                "changed_by_id": item.user_id,
                "changed_by_name": changed_by_name,
                "created_at": item.created_at,
            }

            if _history_search_match(row, search_text):
                rows.append(row)

        if entity_type == "Project":
            current_items = _current_projects(
                actor_data["organisation_id"],
                search_text,
            )
        elif entity_type == "Task":
            current_items = _current_tasks(
                actor_data["organisation_id"],
                search_text,
            )
        else:
            current_items = []

        changers = (
            User.objects
            .filter(
                organisation_id=actor_data["organisation_id"],
                audit_logs__isnull=False,
            )
            .distinct()
            .order_by("first_name", "last_name")
        )

        return Response({
            "items": rows,
            "total": len(rows),
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
