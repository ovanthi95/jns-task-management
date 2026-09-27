from django.db import migrations, models
import django.db.models.deletion


PERMISSIONS = [
    ("manage_users", "Manage users", "Create, edit and deactivate user accounts.", "Administration", 10),
    ("manage_roles", "Manage roles & permissions", "Create roles and configure their permissions.", "Administration", 20),
    ("view_all_projects", "View all projects", "See every project in the organisation.", "Projects", 10),
    ("create_projects", "Create projects", "Create new projects.", "Projects", 20),
    ("edit_projects", "Edit projects", "Edit project details and status.", "Projects", 30),
    ("view_all_tasks", "View all tasks", "See task details across organisation projects.", "Tasks", 10),
    ("create_tasks", "Create tasks", "Create tasks and choose an assignee.", "Tasks", 20),
    ("edit_tasks", "Edit task details", "Edit task title, dates, priority, type and estimates.", "Tasks", 30),
    ("reassign_tasks", "Reassign tasks", "Change the assignee of an existing task.", "Tasks", 40),
    ("change_any_task_status", "Change any task status", "Move any accessible task between workflow statuses.", "Tasks", 50),
    ("complete_assigned_tasks", "Complete assigned tasks", "Mark personally assigned tasks as Completed.", "Tasks", 60),
    ("send_task_notifications", "Send task assignment emails", "Email an assignee when a task is created.", "Tasks", 70),
    ("view_history", "View organisation history", "View the central Project, Task and User history.", "Reporting", 10),
    ("view_workload", "View workload", "View staff workload summaries and user workload details.", "Reporting", 20),
]

DEFAULTS = {
    "admin": {item[0] for item in PERMISSIONS},
    "manager": {
        "view_all_projects",
        "create_projects",
        "edit_projects",
        "view_all_tasks",
        "create_tasks",
        "edit_tasks",
        "change_any_task_status",
        "complete_assigned_tasks",
        "view_workload",
    },
    "employee": {"complete_assigned_tasks"},
    "intern": {"complete_assigned_tasks"},
    "volunteer": {"complete_assigned_tasks"},
}


def seed_permissions(apps, schema_editor):
    Permission = apps.get_model("users", "Permission")
    Role = apps.get_model("users", "Role")
    RolePermission = apps.get_model("users", "RolePermission")

    by_code = {}
    for code, label, description, category, order in PERMISSIONS:
        permission, _ = Permission.objects.update_or_create(
            code=code,
            defaults={
                "label": label,
                "description": description,
                "category": category,
                "display_order": order,
                "is_active": True,
            },
        )
        by_code[code] = permission

    for role in Role.objects.all():
        codes = DEFAULTS.get(role.role_name.lower(), set())
        for code in codes:
            RolePermission.objects.get_or_create(
                role=role,
                permission=by_code[code],
            )
        role.permissions_configured = True
        role.save(update_fields=["permissions_configured"])


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="role",
            name="permissions_configured",
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name="Permission",
            fields=[
                ("permission_id", models.AutoField(primary_key=True, serialize=False)),
                ("code", models.CharField(max_length=80, unique=True)),
                ("label", models.CharField(max_length=120)),
                ("description", models.CharField(blank=True, default="", max_length=255)),
                ("category", models.CharField(max_length=50)),
                ("display_order", models.PositiveSmallIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={
                "db_table": "permissions",
                "ordering": ["category", "display_order", "label"],
            },
        ),
        migrations.CreateModel(
            name="RolePermission",
            fields=[
                ("role_permission_id", models.AutoField(primary_key=True, serialize=False)),
                ("permission", models.ForeignKey(
                    db_column="permission_id",
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="role_permissions",
                    to="users.permission",
                )),
                ("role", models.ForeignKey(
                    db_column="role_id",
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="role_permissions",
                    to="users.role",
                )),
            ],
            options={
                "db_table": "role_permissions",
                "constraints": [
                    models.UniqueConstraint(
                        fields=("role", "permission"),
                        name="unique_role_permission",
                    )
                ],
            },
        ),
        migrations.RunPython(seed_permissions, migrations.RunPython.noop),
    ]
