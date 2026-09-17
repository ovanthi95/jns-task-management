from django.db import models
from users.models import Organisation, User


class AuditLog(models.Model):
    audit_log_id = models.AutoField(primary_key=True)

    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.PROTECT,
        db_column="organisation_id",
        related_name="audit_logs"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="user_id",
        related_name="audit_logs"
    )

    action = models.CharField(max_length=50)

    entity_type = models.CharField(max_length=50)

    entity_id = models.IntegerField(
        null=True,
        blank=True
    )

    description = models.CharField(
        max_length=500,
        null=True,
        blank=True
    )

    old_value = models.JSONField(
        null=True,
        blank=True
    )

    new_value = models.JSONField(
        null=True,
        blank=True
    )

    ip_address = models.CharField(
        max_length=45,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_logs"

    def __str__(self):
        return f"{self.action} - {self.entity_type}"