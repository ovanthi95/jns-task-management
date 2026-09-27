"""Supporting task-form lookup endpoint."""

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from projects.models import Project, ProjectMember
from tasks.models import Priority, TaskStatus, TaskType
from users.models import User
from users.services.permission_service import actor_has_permission
from users.services.session_service import get_authenticated_session_user


class ProjectTaskOptionsView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, project_id):
        actor = get_authenticated_session_user(
            request.session.get("user_id")
        )

        if actor is None:
            request.session.flush()
            return Response(
                {"detail": "Not authenticated."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        projects = Project.objects.filter(
            organisation_id=actor["organisation_id"],
        )

        if not actor_has_permission(actor, "view_all_projects"):
            projects = projects.filter(
                members__user_id=actor["user_id"],
            ).distinct()

        project = get_object_or_404(
            projects,
            project_id=project_id,
        )

        can_create = actor_has_permission(actor, "create_tasks")
        can_reassign = actor_has_permission(actor, "reassign_tasks")
        can_manage_tasks = can_create or can_reassign

        member_ids = ProjectMember.objects.filter(
            project_id=project_id,
        ).values_list("user_id", flat=True)

        users = (
            User.objects
            .filter(
                user_id__in=member_ids,
                organisation_id=actor["organisation_id"],
                status__iexact="Active",
            )
            .select_related("role")
            .order_by("first_name", "last_name")
            if can_manage_tasks
            else User.objects.none()
        )

        return Response({
            "project": {
                "project_id": project.project_id,
                "project_name": project.project_name,
                "status": project.status,
            },
            "current_user": {
                "user_id": actor["user_id"],
                "role_name": actor["role_name"],
                "permissions": sorted(actor.get("permissions") or []),
            },
            "can_create": can_create and project.status == "Active",
            "task_types": list(
                TaskType.objects.filter(is_active=True)
                .order_by("display_order", "type_name")
                .values("task_type_id", "type_name")
            ),
            "task_statuses": list(
                TaskStatus.objects.filter(is_active=True)
                .order_by("display_order", "status_name")
                .values("status_id", "status_name")
            ),
            "priorities": list(
                Priority.objects.filter(is_active=True)
                .order_by("display_order", "priority_name")
                .values("priority_id", "priority_name")
            ),
            "users": [
                {
                    "user_id": item.user_id,
                    "name": f"{item.first_name} {item.last_name}".strip(),
                    "role_name": item.role.role_name if item.role else "",
                    "email": item.email,
                }
                for item in users
            ],
        })
