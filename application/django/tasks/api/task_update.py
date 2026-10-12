"""API 08 - PATCH /api/tasks/:taskId."""

from django.db import DatabaseError
from tasks.models import Task, TaskAssignee
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from tasks.serializers import TaskSerializer
from tasks.services.exceptions import InvalidTaskInput
from tasks.services.task_notification_service import send_task_update_email
from users.services.permission_service import actor_has_permission
from tasks.services.task_update_service import (
    TaskNotVisible,
    TaskUpdateNotPermitted,
    update_task_details,
)


class TaskUpdateSerializer(serializers.Serializer):
    """Only fields explicitly owned by API 08 may be patched."""

    notify_assignee = serializers.BooleanField(required=False)
    title = serializers.CharField(
        max_length=200,
        trim_whitespace=True,
        required=False,
    )
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )
    task_type_id = serializers.IntegerField(min_value=1, required=False)
    other_task_type = serializers.CharField(
        max_length=100,
        required=False,
        allow_null=True,
        allow_blank=True,
    )
    priority_id = serializers.IntegerField(min_value=1, required=False)
    assignee_id = serializers.IntegerField(min_value=1, required=False)
    start_date = serializers.DateField(required=False, allow_null=True)
    due_date = serializers.DateField(required=False, allow_null=True)
    estimated_hours = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        min_value=0,
        required=False,
        allow_null=True,
    )
    status_id = serializers.IntegerField(min_value=1, required=False)

    def to_internal_value(self, data):
        if hasattr(data, "keys"):
            forbidden = sorted(set(data.keys()) - set(self.fields.keys()))

            if forbidden:
                raise serializers.ValidationError({
                    field: ["This field cannot be updated."]
                    for field in forbidden
                })

        return super().to_internal_value(data)

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError(
                "Provide at least one field to update."
            )

        start_date = attrs.get("start_date")
        due_date = attrs.get("due_date")

        if (
            "start_date" in attrs
            and "due_date" in attrs
            and start_date
            and due_date
            and due_date < start_date
        ):
            raise serializers.ValidationError(
                {"due_date": "Due date cannot be before the start date."}
            )

        return attrs


class TaskUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, task_id):
        serializer = TaskUpdateSerializer(
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)

        actor = {
            "user_id": request.user.user_id,
            "organisation_id": request.user.organisation_id,
            "role_name": request.user.role.role_name,
            "permissions": list(
                getattr(request.user, "permissions", []) or []
            ),
        }

        changes = dict(serializer.validated_data)
        notify_assignee = changes.pop("notify_assignee", False)
        if notify_assignee and not actor_has_permission(
            {"role_name": request.user.role.role_name},
            "send_task_notifications",
        ):
            return Response(
                {"detail": "Task notification permission required."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not changes:
            return Response(
                {"detail": "Provide at least one task change."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        before = None
        if notify_assignee:
            before = Task.objects.filter(task_id=task_id).first()
            if before:
                before_values = {field: getattr(before, field) for field in changes if hasattr(before, field)}
                before_assignee = TaskAssignee.objects.filter(task_id=task_id).values_list("user_id", flat=True).first()

        try:
            task = update_task_details(
                actor=actor,
                task_id=task_id,
                changes=changes,
            )
        except TaskNotVisible:
            return Response(
                {"detail": "Not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except TaskUpdateNotPermitted:
            return Response(
                {"detail": "You do not have permission for this task change."},
                status=status.HTTP_403_FORBIDDEN,
            )
        except InvalidTaskInput as error:
            return Response(
                error.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )
        except DatabaseError as error:
            return _database_error_response(error)

        response_data = dict(TaskSerializer(task).data)
        if notify_assignee:
            response_data["email_requested"] = True
            response_data["email_sent"] = False
            after = Task.objects.filter(task_id=task_id).first()
            actual_changes = {}
            if before and after:
                for field, old in before_values.items():
                    new = getattr(after, field)
                    if old != new:
                        actual_changes[field] = (old, new)
                if "assignee_id" in changes:
                    current_assignee = TaskAssignee.objects.filter(task_id=task_id).values_list("user_id", flat=True).first()
                    if before_assignee != current_assignee:
                        actual_changes["assignee_id"] = (before_assignee, current_assignee)
            if actual_changes:
                try:
                    response_data["email_sent"] = send_task_update_email(
                        task_id=task_id,
                        updated_by_id=request.user.user_id,
                        changes=actual_changes,
                    )
                    if not response_data["email_sent"]:
                        response_data["email_warning"] = "Task updated, but no email was sent to the assignee."
                except Exception:
                    response_data["email_warning"] = "Task updated, but the notification email could not be sent."
        return Response(response_data, status=status.HTTP_200_OK)


def _database_error_response(error):
    """Map defensive stored-procedure validation to the public API shape."""
    message = str(error).lower()

    if "task not found" in message:
        return Response(
            {"detail": "Not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    mappings = (
        ("task title is required", "title", "Task title is required."),
        ("invalid task type", "task_type_id", "No active task type with that id."),
        ("invalid priority", "priority_id", "No active priority with that id."),
        ("invalid assignee", "assignee_id", "That user cannot be assigned to this project."),
        ("invalid estimated hours", "estimated_hours", "Estimated hours cannot be negative."),
        ("due date cannot be before start date", "due_date", "Due date cannot be before the start date."),
        ("invalid task status", "status_id", "No active status with that id."),
    )

    for needle, field, detail in mappings:
        if needle in message:
            return Response(
                {field: [detail]},
                status=status.HTTP_400_BAD_REQUEST,
            )

    raise error
