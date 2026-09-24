"""Wire shapes for the two task services on the agreed REST list:

    API 06  POST /api/projects/:projectId/tasks
    API 07  GET  /api/projects/:projectId/tasks

Nothing else is defined here. The other services belong to other cards.

These are plain Serializers, not ModelSerializers, and that is deliberate.
Under the agreed layering the database is reached through stored procedures,
so there is no model instance for a serializer to bind to: the read
serializers are handed the dictionaries the procedures returned, and the write
serializer only parses and type-checks a request body. Nothing in this file
touches the ORM or writes anything.

Two rules this file follows:

1. The client never sends project_id or created_by. The endpoint derives the
   first from the URL and the second from the session, so a forged request
   body cannot put a task in another organisation's project.
2. Every field is written out. Nothing is generated from a model, so no column
   added to a table later can appear in a response by accident.
"""

from rest_framework import serializers


class TaskAssigneeSerializer(serializers.Serializer):
    """One assignment, flattened for the client.

    Only the four fields the agreed read contract names. The stored procedure
    selects exactly these, so a user's email or password hash has no path into
    this response.
    """

    user_id = serializers.IntegerField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    assignment_role = serializers.CharField(read_only=True)


class TaskSerializer(serializers.Serializer):
    """Read shape. Returned by API 07, and by API 06 after the insert.

    Each lookup is returned as both its id and its name so the client can
    display a task without a second request per row.

    `assignees` is an array even though API 06 accepts exactly one
    `assignee_id`. A task can hold several assignments, so the read contract is
    written for that shape now and will not have to change when a later
    service assigns more than one person.
    """

    task_id = serializers.IntegerField(read_only=True)
    project_id = serializers.IntegerField(read_only=True)

    task_type_id = serializers.IntegerField(read_only=True)
    task_type_name = serializers.CharField(read_only=True)

    status_id = serializers.IntegerField(read_only=True)
    status_name = serializers.CharField(read_only=True)

    priority_id = serializers.IntegerField(read_only=True)
    priority_name = serializers.CharField(read_only=True)

    title = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)

    start_date = serializers.DateField(read_only=True)
    due_date = serializers.DateField(read_only=True)

    # Rendered as a string ("4.50"), which is DRF's default for decimals and
    # is what the agreed contract publishes. Floats would lose the scale.
    estimated_hours = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        read_only=True,
    )
    actual_hours = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        read_only=True,
    )

    assignees = TaskAssigneeSerializer(many=True, read_only=True)

    created_by_id = serializers.IntegerField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class TaskCreateSerializer(serializers.Serializer):
    """Write shape for API 06. Parsing and types only.

    What this serializer answers: is the field present, is it the right type,
    is it the right length, and are the two dates in a sensible order.

    What it deliberately does not answer: whether the ids name rows that
    exist, and whether the assignee may be given work on this project. Those
    need the database, so they belong to the service, which resolves them
    through stored procedures.

    The three lookup fields are required. The columns are NOT NULL with no
    default, so there is no value this layer could pick on the caller's behalf
    without inventing one.

    `assignee_id` is required as well. API 06 is "create and assign a task", so
    a task cannot be created through this service without an assignee. Exactly
    one is accepted: a task can hold several assignments, but the agreed
    contract for this card creates one.
    """

    task_type_id = serializers.IntegerField()
    status_id = serializers.IntegerField()
    priority_id = serializers.IntegerField()
    assignee_id = serializers.IntegerField()

    title = serializers.CharField(max_length=200)

    description = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
    )

    start_date = serializers.DateField(required=False, allow_null=True)
    due_date = serializers.DateField(required=False, allow_null=True)

    estimated_hours = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        required=False,
        allow_null=True,
    )

    def validate_title(self, value):
        """A title of nothing but spaces is a blank title.

        CharField already rejects "", but "   " passes it, so the stripped
        value is what gets checked and what gets stored.
        """
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
