from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tasks", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="task",
            name="other_task_type",
            field=models.CharField(
                max_length=100,
                null=True,
                blank=True,
            ),
        ),
    ]
