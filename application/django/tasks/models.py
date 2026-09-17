from django.db import models
from users.models import User
from projects.models import Project


class TaskType(models.Model):
    task_type_id = models.AutoField(primary_key=True)

    type_name = models.CharField(
        max_length=50,
        unique=True
    )

    description = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    is_active = models.BooleanField(default=True)
    display_order = models.PositiveSmallIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "task_types"

    def __str__(self):
        return self.type_name


class TaskStatus(models.Model):
    status_id = models.AutoField(primary_key=True)

    status_name = models.CharField(
        max_length=50,
        unique=True
    )

    description = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    is_active = models.BooleanField(default=True)
    is_terminal = models.BooleanField(default=False)
    display_order = models.PositiveSmallIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "task_statuses"

    def __str__(self):
        return self.status_name


class Priority(models.Model):
    priority_id = models.AutoField(primary_key=True)

    priority_name = models.CharField(
        max_length=30,
        unique=True
    )

    priority_level = models.PositiveSmallIntegerField()
    display_order = models.PositiveSmallIntegerField(default=0)

    colour = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "priorities"

    def __str__(self):
        return self.priority_name


class Task(models.Model):
    task_id = models.AutoField(primary_key=True)

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        db_column="project_id",
        related_name="tasks"
    )

    task_type = models.ForeignKey(
        TaskType,
        on_delete=models.PROTECT,
        db_column="task_type_id",
        related_name="tasks"
    )

    status = models.ForeignKey(
        TaskStatus,
        on_delete=models.PROTECT,
        db_column="status_id",
        related_name="tasks"
    )

    priority = models.ForeignKey(
        Priority,
        on_delete=models.PROTECT,
        db_column="priority_id",
        related_name="tasks"
    )

    title = models.CharField(max_length=200)

    description = models.TextField(
        null=True,
        blank=True
    )

    start_date = models.DateField(
        null=True,
        blank=True
    )

    due_date = models.DateField(
        null=True,
        blank=True
    )

    estimated_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True
    )

    actual_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        db_column="created_by",
        related_name="created_tasks"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tasks"

    def __str__(self):
        return self.title


class TaskAssignee(models.Model):
    task_assignee_id = models.AutoField(primary_key=True)

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        db_column="task_id",
        related_name="assignees"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_column="user_id",
        related_name="assigned_tasks"
    )

    assignment_role = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    assigned_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        db_column="assigned_by",
        related_name="task_assignments_made"
    )

    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "task_assignees"

        constraints = [
            models.UniqueConstraint(
                fields=["task", "user"],
                name="unique_task_user"
            )
        ]

    def __str__(self):
        return f"{self.task.title} - {self.user}"


class Comment(models.Model):
    comment_id = models.AutoField(primary_key=True)

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        db_column="task_id",
        related_name="comments"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        db_column="user_id",
        related_name="comments"
    )

    comment_text = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "comments"

    def __str__(self):
        return f"Comment {self.comment_id} on {self.task.title}"


class Attachment(models.Model):
    attachment_id = models.AutoField(primary_key=True)

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        db_column="task_id",
        related_name="attachments"
    )

    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        db_column="uploaded_by",
        related_name="uploaded_attachments"
    )

    file_name = models.CharField(max_length=255)

    file_type = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    file_size = models.PositiveBigIntegerField(
        null=True,
        blank=True
    )

    s3_key = models.CharField(max_length=500)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "attachments"

    def __str__(self):
        return self.file_name


class TaskHistory(models.Model):
    history_id = models.AutoField(primary_key=True)

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        db_column="task_id",
        related_name="history"
    )

    changed_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        db_column="changed_by",
        related_name="task_changes"
    )

    field_name = models.CharField(max_length=100)

    old_value = models.JSONField(
        null=True,
        blank=True
    )

    new_value = models.JSONField(
        null=True,
        blank=True
    )

    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "task_history"

    def __str__(self):
        return f"{self.task.title} - {self.field_name}"