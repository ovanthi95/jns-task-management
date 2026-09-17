from django.db import models
from users.models import Organisation, User


class Project(models.Model):
    project_id = models.AutoField(primary_key=True)

    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.PROTECT,
        db_column="organisation_id",
        related_name="projects"
    )

    project_name = models.CharField(max_length=150)

    description = models.TextField(
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=30,
        default="Active"
    )

    start_date = models.DateField(
        null=True,
        blank=True
    )

    end_date = models.DateField(
        null=True,
        blank=True
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        db_column="created_by",
        related_name="created_projects"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "projects"

    def __str__(self):
        return self.project_name


class ProjectMember(models.Model):
    project_member_id = models.AutoField(primary_key=True)

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        db_column="project_id",
        related_name="members"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_column="user_id",
        related_name="project_memberships"
    )

    project_role = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "project_members"

        constraints = [
            models.UniqueConstraint(
                fields=["project", "user"],
                name="unique_project_user"
            )
        ]

    def __str__(self):
        return f"{self.project.project_name} - {self.user}"