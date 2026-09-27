"""API 08 - PATCH /api/tasks/:taskId."""

from django.db import DatabaseError
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from tasks.serializers import TaskSerializer
from tasks.services.exceptions import InvalidTaskInput
from tasks.services.task_update_service import (
    TaskNotVisible,
    TaskUpdateNotPermitted,
    update_task_details,
)
from ._session import not_authenticated, session_user


class TaskUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200, trim_whitespace=True, required=False)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    task_type_id = serializers.IntegerField(min_value=1, required=False)
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
            raise serializers.ValidationError({
                "due_date": ["Due date cannot be before the start date."]
            })

        return attrs


class TaskUpdateView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def patch(self, request, task_id):
        actor = session_user(request)

        if actor is None:
            return not_authenticated()

        serializer = TaskUpdateSerializer(
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)

        try:
            task = update_task_details(
                actor=actor,
                task_id=task_id,
                changes=dict(serializer.validated_data),
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

        return Response(
            TaskSerializer(task).data,
            status=status.HTTP_200_OK,
        )


def _database_error_response(error):
    message = str(error).lower()

    mappings = (
        ("task not found", "detail", "Not found.", 404),
        ("task title is required", "title", "Task title is required.", 400),
        ("invalid task type", "task_type_id", "Choose an active task type.", 400),
        ("invalid priority", "priority_id", "Choose an active priority.", 400),
        ("invalid assignee", "assignee_id", "Choose an active project member.", 400),
        ("invalid estimated hours", "estimated_hours", "Estimated hours cannot be negative.", 400),
        ("due date cannot be before start date", "due_date", "Due date cannot be before the start date.", 400),
        ("invalid task status", "status_id", "Choose an active task status.", 400),
    )

    for needle, field, detail, status_code in mappings:
        if needle in message:
            payload = {"detail": detail} if field == "detail" else {field: [detail]}
            return Response(payload, status=status_code)

    raise error
