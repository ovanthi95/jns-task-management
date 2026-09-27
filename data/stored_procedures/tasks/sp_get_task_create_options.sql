-- API 06 support data for the create-task form.

DROP PROCEDURE IF EXISTS sp_get_task_create_options;

DELIMITER $

CREATE PROCEDURE sp_get_task_create_options (
    IN p_project_id INT
)
BEGIN
    SELECT
        'project' AS option_group,
        p.project_id AS option_id,
        p.project_name AS option_name,
        p.status AS extra_name
    FROM projects p
    WHERE p.project_id = p_project_id

    UNION ALL

    SELECT
        'task_type',
        tt.task_type_id,
        tt.type_name,
        NULL
    FROM task_types tt
    WHERE tt.is_active = 1

    UNION ALL

    SELECT
        'priority',
        pr.priority_id,
        pr.priority_name,
        NULL
    FROM priorities pr
    WHERE pr.is_active = 1

    UNION ALL

    SELECT
        'new_status',
        ts.status_id,
        ts.status_name,
        NULL
    FROM task_statuses ts
    WHERE ts.is_active = 1
      AND LOWER(ts.status_name) = 'new'

    UNION ALL

    SELECT
        'user',
        u.user_id,
        CONCAT(TRIM(u.first_name), ' ', TRIM(u.last_name)),
        r.role_name
    FROM project_members pm
    INNER JOIN users u
        ON u.user_id = pm.user_id
    INNER JOIN roles r
        ON r.role_id = u.role_id
    WHERE pm.project_id = p_project_id
      AND LOWER(u.status) = 'active'

    ORDER BY option_group, option_name;
END$

DELIMITER ;
