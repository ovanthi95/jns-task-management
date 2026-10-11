from django.db import migrations

SP_GET_USER_WORKLOAD = r"""
DROP PROCEDURE IF EXISTS sp_get_user_workload;

CREATE PROCEDURE sp_get_user_workload(
    IN p_organisation_id BIGINT,
    IN p_user_id BIGINT
)
BEGIN
    SELECT
        u.user_id,
        u.first_name,
        u.last_name,
        u.email,
        r.role_name,
        u.availability,
        COUNT(DISTINCT CASE
            WHEN p.status = 'Active' AND ts.status_name <> 'Completed'
            THEN t.task_id END) AS active_tasks,
        COUNT(DISTINCT CASE
            WHEN p.status = 'Active' THEN t.task_id END) AS assigned_tasks,
        COUNT(DISTINCT CASE
            WHEN p.status = 'Active' AND ts.status_name = 'Completed'
            THEN t.task_id END) AS completed_tasks,
        COUNT(DISTINCT CASE
            WHEN p.status = 'Active'
             AND ts.status_name <> 'Completed'
             AND t.due_date IS NOT NULL
             AND t.due_date < CURDATE()
            THEN t.task_id END) AS overdue_tasks,
        COUNT(DISTINCT CASE
            WHEN p.status = 'Active'
             AND ts.status_name <> 'Completed'
             AND t.due_date IS NOT NULL
             AND t.due_date >= CURDATE()
             AND t.due_date <= DATE_ADD(CURDATE(), INTERVAL 7 DAY)
            THEN t.task_id END) AS due_soon_tasks,
        COALESCE(SUM(CASE
            WHEN p.status = 'Active' AND ts.status_name <> 'Completed'
            THEN COALESCE(t.estimated_hours, 0)
            ELSE 0 END), 0) AS estimated_hours,
        COUNT(DISTINCT CASE
            WHEN p.status = 'Active' AND ts.status_name <> 'Completed'
            THEN p.project_id END) AS project_count,
        GROUP_CONCAT(
            DISTINCT CASE
                WHEN p.status = 'Active' AND ts.status_name <> 'Completed'
                THEN p.project_name END
            ORDER BY p.project_name SEPARATOR '||'
        ) AS current_projects
    FROM users u
    JOIN roles r ON r.role_id = u.role_id
    LEFT JOIN task_assignees ta ON ta.user_id = u.user_id
    LEFT JOIN tasks t ON t.task_id = ta.task_id
    LEFT JOIN projects p
        ON p.project_id = t.project_id
       AND p.organisation_id = p_organisation_id
    LEFT JOIN task_statuses ts ON ts.status_id = t.status_id
    WHERE u.organisation_id = p_organisation_id
      AND u.user_id = p_user_id
      AND LOWER(u.status) = 'active'
    GROUP BY
        u.user_id, u.first_name, u.last_name, u.email,
        r.role_name, u.availability;
END
"""


def create_user_workload_procedure(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        for statement in SP_GET_USER_WORKLOAD.strip().split(";"):
            statement = statement.strip()
            if statement:
                cursor.execute(statement)


def drop_user_workload_procedure(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("DROP PROCEDURE IF EXISTS sp_get_user_workload")


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0002_rbac_permissions"),
    ]

    operations = [
        migrations.RunPython(
            create_user_workload_procedure,
            drop_user_workload_procedure,
        ),
    ]
