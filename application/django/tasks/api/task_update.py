"""API 08 - PATCH /api/tasks/:taskId."""

from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from tasks.serializers import TaskSerializer
from tasks.services.exceptions import InvalidTaskInput
from tasks.services.task_update_service import (
    TaskNotVisible,
    TaskUpdateNotPermitted,
    update_task_details,
)


class TaskUpdateSerializer(serializers.Serializer):
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
        }

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

        return Response(
            TaskSerializer(task).data,
            status=status.HTTP_200_OK,
        )
