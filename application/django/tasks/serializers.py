"""
Serializers for the two task services on the agreed REST list:

    API 06  POST /api/projects/:projectId/tasks
    API 07  GET  /api/projects/:projectId/tasks

Nothing else is implemented here. The other services belong to other cards.

Two rules this file follows:

1. The client never sends organisation_id or created_by. The view derives both
   from the authenticated user, so a forged request body cannot put a task in
   another organisation's project.
2. Field names on the wire end in _id and match the React form exactly
   (presentation/react/src/views/tasks/CreateTask.jsx). The model field is
   reached through `source`, so renaming one side does not break the other.
"""

from rest_framework import serializers

from .models import Priority, Task, TaskStatus, TaskType


class TaskSerializer(serializers.ModelSerializer):
    """Read shape. Returned by API 07, and by API 06 after the insert.

    Each lookup is returned as both its id and its name so the client can
    display a task without a second request per row.
    """

    project_id = serializers.IntegerField(
        source="project.project_id",
        read_only=True,
    )

    task_type_id = serializers.IntegerField(
        source="task_type.task_type_id",
        read_only=True,
    )
    task_type_name = serializers.CharField(
        source="task_type.type_name",
        read_only=True,
    )

    status_id = serializers.IntegerField(
        source="status.status_id",
        read_only=True,
    )
    status_name = serializers.CharField(
        source="status.status_name",
        read_only=True,
    )

    priority_id = serializers.IntegerField(
        source="priority.priority_id",
        read_only=True,
    )
    priority_name = serializers.CharField(
        source="priority.priority_name",
        read_only=True,
    )

    created_by_id = serializers.IntegerField(
        source="created_by.user_id",
        read_only=True,
    )

    class Meta:
        model = Task

        fields = [
            "task_id",
            "project_id",
            "task_type_id",
            "task_type_name",
            "status_id",
            "status_name",
            "priority_id",
            "priority_name",
            "title",
            "description",
            "start_date",
            "due_date",
            "estimated_hours",
            "actual_hours",
            "created_by_id",
            "created_at",
            "updated_at",
        ]


class TaskCreateSerializer(serializers.ModelSerializer):
    """Write shape for API 06.

    `project` and `created_by` are absent on purpose: the view supplies them.

    The three lookup fields are required. The database declares them NOT NULL
    with no default, so there is no value this layer could pick on the caller's
    behalf without inventing one.
    """

    task_type_id = serializers.PrimaryKeyRelatedField(
        source="task_type",
        queryset=TaskType.objects.all(),
    )

    status_id = serializers.PrimaryKeyRelatedField(
        source="status",
        queryset=TaskStatus.objects.all(),
    )

    priority_id = serializers.PrimaryKeyRelatedField(
        source="priority",
        queryset=Priority.objects.all(),
    )

    class Meta:
        model = Task

        fields = [
            "task_type_id",
            "status_id",
            "priority_id",
            "title",
            "description",
            "start_date",
            "due_date",
            "estimated_hours",
        ]

    def validate_title(self, value):
        title = value.strip()

        if not title:
            raise serializers.ValidationError("Title cannot be blank.")

        return title

    def validate(self, attrs):
        start_date = attrs.get("start_date")
        due_date = attrs.get("due_date")

        if start_date and due_date and due_date < start_date:
            raise serializers.ValidationError(
                {"due_date": "Due date cannot be before the start date."}
            )

        return attrs
