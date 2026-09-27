from django.db import migrations, models
import django.db.models.deletion


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
            options={"db_table": "role_permissions"},
        ),
        migrations.AddConstraint(
            model_name="rolepermission",
            constraint=models.UniqueConstraint(
                fields=("role", "permission"),
                name="unique_role_permission",
            ),
        ),
    ]
