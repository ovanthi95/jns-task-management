"""
Serializers for the two task services on the agreed REST list:

    API 06  POST /api/projects/:projectId/tasks
    API 07  GET  /api/projects/:projectId/tasks

Nothing else is implemented here. The other services belong to other cards.

Two rules this file follows:

1. The client never sends organisation_id or created_by. The view derives both
   from the authenticated user, so a forged request body cannot put a task in
   another organisation's project.
2. Each lookup is exposed on the wire as <name>_id. The model field is reached
   through `source`, so the wire name and the model field name can change
   independently of one another.
"""

from django.db import transaction
from rest_framework import serializers

from projects.models import ProjectMember
from users.models import User

from .models import Priority, Task, TaskAssignee, TaskStatus, TaskType


class TaskAssigneeSerializer(serializers.ModelSerializer):
    """One row of task_assignees, flattened for the client.

    Only the four fields the agreed read contract names. The user's email and
    password hash are both reachable from here through the foreign key, so the
    field list is written out rather than left to `__all__`: a field added to
    the User model later cannot leak into this response by accident.
    """

    user_id = serializers.IntegerField(
        source="user.user_id",
        read_only=True,
    )
    first_name = serializers.CharField(
        source="user.first_name",
        read_only=True,
    )
    last_name = serializers.CharField(
        source="user.last_name",
        read_only=True,
    )

    class Meta:
        model = TaskAssignee

        fields = [
            "user_id",
            "first_name",
            "last_name",
            "assignment_role",
        ]


class TaskSerializer(serializers.ModelSerializer):
    """Read shape. Returned by API 07, and by API 06 after the insert.

    Each lookup is returned as both its id and its name so the client can
    display a task without a second request per row.

    `assignees` is an array even though API 06 accepts exactly one
    `assignee_id`. task_assignees can hold several rows per task, so the read
    contract is written for that shape now and will not have to change when a
    later service assigns more than one person.
    """

    assignees = TaskAssigneeSerializer(
        many=True,
        read_only=True,
    )

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
            "assignees",
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

    `assignee_id` is required as well. API 06 is "create and assign a task", so
    a task cannot be created through this service without an assignee. Exactly
    one is accepted: task_assignees can hold several rows per task, but the
    agreed contract for this card creates one.
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

    assignee_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True,
    )

    class Meta:
        model = Task

        fields = [
            "task_type_id",
            "status_id",
            "priority_id",
            "assignee_id",
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

    def validate_assignee_id(self, user):
        """The assignee has to be someone who can work on this project.

        PrimaryKeyRelatedField has already rejected an id matching no user, so
        what is left is that the user is in this project's organisation and
        holds a ProjectMember row for it. Project.created_by is deliberately
        not accepted as implicit membership.
        """

        project = self.context["project"]

        if user.organisation_id != project.organisation_id:
            raise serializers.ValidationError(
                "That user does not belong to this project's organisation."
            )

        is_member = ProjectMember.objects.filter(
            project=project,
            user=user,
        ).exists()

        if not is_member:
            raise serializers.ValidationError(
                "That user is not a member of this project."
            )

        return user

    def validate(self, attrs):
        start_date = attrs.get("start_date")
        due_date = attrs.get("due_date")

        if start_date and due_date and due_date < start_date:
            raise serializers.ValidationError(
                {"due_date": "Due date cannot be before the start date."}
            )

        return attrs

    def create(self, validated_data):
        """Write the task and its assignment together, or write neither.

        Without the transaction, a failure on the second insert would leave a
        task with no assignee behind, which is exactly the state API 06 is not
        allowed to produce.
        """

        assignee = validated_data.pop("assignee_id")

        with transaction.atomic():
            task = Task.objects.create(**validated_data)

            TaskAssignee.objects.create(
                task=task,
                user=assignee,
                assigned_by=validated_data["created_by"],
                # assignment_role stays NULL: the contract does not define
                # any values for it yet.
            )

        return task
