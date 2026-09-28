DROP PROCEDURE IF EXISTS sp_get_user_workload_tasks;

DELIMITER $$

CREATE PROCEDURE sp_get_user_workload_tasks(
    IN p_organisation_id BIGINT,
    IN p_user_id BIGINT
)
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM users
        WHERE user_id = p_user_id
          AND organisation_id = p_organisation_id
    ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'User not found';
    END IF;

    SELECT
        t.task_id,
        t.title,
        p.project_id,
        p.project_name,
        ts.status_name,
        pr.priority_name,
        t.start_date,
        t.due_date,
        t.estimated_hours,
        CASE
            WHEN t.due_date IS NOT NULL
             AND t.due_date < CURDATE()
            THEN 1
            ELSE 0
        END AS is_overdue,
        CASE
            WHEN t.due_date IS NOT NULL
             AND t.due_date >= CURDATE()
             AND t.due_date <= DATE_ADD(CURDATE(), INTERVAL 7 DAY)
            THEN 1
            ELSE 0
        END AS is_due_soon
    FROM task_assignees ta
    JOIN tasks t ON t.task_id = ta.task_id
    JOIN projects p ON p.project_id = t.project_id
    JOIN task_statuses ts ON ts.status_id = t.status_id
    JOIN priorities pr ON pr.priority_id = t.priority_id
    WHERE ta.user_id = p_user_id
      AND p.organisation_id = p_organisation_id
      AND p.status = 'Active'
      AND ts.status_name <> 'Completed'
    ORDER BY
        is_overdue DESC,
        CASE WHEN t.due_date IS NULL THEN 1 ELSE 0 END,
        t.due_date,
        pr.priority_level DESC,
        t.title,
        t.task_id;
END$$

DELIMITER ;
