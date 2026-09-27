from datetime import timedelta

from django.db import migrations


def status_name(value):
    if isinstance(value, dict):
        return value.get("status_name") or value.get("name") or str(value)
    return value


def backfill_task_history(apps, schema_editor):
    AuditLog = apps.get_model("audit", "AuditLog")
    TaskHistory = apps.get_model("tasks", "TaskHistory")

    rows = (
        TaskHistory.objects
        .select_related("task__project")
        .order_by("changed_at", "history_id")
    )

    for item in rows:
        start = item.changed_at - timedelta(seconds=5)
        end = item.changed_at + timedelta(seconds=5)

        exists = AuditLog.objects.filter(
            organisation_id=item.task.project.organisation_id,
            user_id=item.changed_by_id,
            entity_type="Task",
            entity_id=item.task_id,
            field_name=item.field_name,
            created_at__gte=start,
            created_at__lte=end,
        ).exists()

        if exists:
            continue

        old_value = status_name(item.old_value)
        new_value = status_name(item.new_value)

        created = AuditLog.objects.create(
            organisation_id=item.task.project.organisation_id,
            user_id=item.changed_by_id,
            action="Updated",
            entity_type="Task",
            entity_id=item.task_id,
            entity_name=item.task.title,
            field_name=item.field_name,
            description=(
                f'Updated task "{item.task.title}" '
                f'in project "{item.task.project.project_name}".'
            ),
            old_value=old_value,
            new_value=new_value,
        )

        AuditLog.objects.filter(
            audit_log_id=created.audit_log_id
        ).update(created_at=item.changed_at)


class Migration(migrations.Migration):
    dependencies = [
        ("audit", "0002_history_metadata"),
        ("tasks", "0001_initial"),
        ("projects", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            backfill_task_history,
            migrations.RunPython.noop,
        ),
    ]
