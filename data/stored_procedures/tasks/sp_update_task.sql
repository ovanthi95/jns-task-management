-- API 08
-- Endpoint: PATCH /api/tasks/:taskId

DROP PROCEDURE IF EXISTS sp_update_task;

DELIMITER $$

CREATE PROCEDURE sp_update_task(
    IN p_task_id INT,
    IN p_organisation_id INT,
    IN p_changed_by INT,
    IN p_title_supplied TINYINT,
    IN p_title VARCHAR(200),
    IN p_description_supplied TINYINT,
    IN p_description TEXT,
    IN p_task_type_supplied TINYINT,
    IN p_task_type_id INT,
    IN p_priority_supplied TINYINT,
    IN p_priority_id INT,
    IN p_assignee_supplied TINYINT,
    IN p_assignee_id INT,
    IN p_start_date_supplied TINYINT,
    IN p_start_date DATE,
    IN p_due_date_supplied TINYINT,
    IN p_due_date DATE,
    IN p_estimated_hours_supplied TINYINT,
    IN p_estimated_hours DECIMAL(6,2),
    IN p_status_supplied TINYINT,
    IN p_status_id INT
)
BEGIN
    DECLARE v_project_id INT;
    DECLARE v_current_start DATE;
    DECLARE v_current_due DATE;
    DECLARE v_effective_start DATE;
    DECLARE v_effective_due DATE;

    SELECT
        t.project_id,
        t.start_date,
        t.due_date
    INTO
        v_project_id,
        v_current_start,
        v_current_due
    FROM tasks t
    INNER JOIN projects p
        ON p.project_id = t.project_id
    WHERE t.task_id = p_task_id
      AND p.organisation_id = p_organisation_id
    LIMIT 1;

    IF v_project_id IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Task not found';
    END IF;

    IF p_title_supplied = 1
       AND (p_title IS NULL OR TRIM(p_title) = '') THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Task title is required';
    END IF;

    IF p_task_type_supplied = 1
       AND NOT EXISTS (
            SELECT 1
            FROM task_types
            WHERE task_type_id = p_task_type_id
              AND is_active = 1
       ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Invalid task type';
    END IF;

    IF p_priority_supplied = 1
       AND NOT EXISTS (
            SELECT 1
            FROM priorities
            WHERE priority_id = p_priority_id
              AND is_active = 1
       ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Invalid priority';
    END IF;

    IF p_assignee_supplied = 1
       AND NOT EXISTS (
            SELECT 1
            FROM users u
            INNER JOIN project_members pm
                ON pm.user_id = u.user_id
               AND pm.project_id = v_project_id
            WHERE u.user_id = p_assignee_id
              AND u.organisation_id = p_organisation_id
              AND LOWER(u.status) = 'active'
       ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Invalid assignee';
    END IF;

    IF p_estimated_hours_supplied = 1
       AND p_estimated_hours IS NOT NULL
       AND p_estimated_hours < 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Invalid estimated hours';
    END IF;

    SET v_effective_start = IF(
        p_start_date_supplied = 1,
        p_start_date,
        v_current_start
    );

    SET v_effective_due = IF(
        p_due_date_supplied = 1,
        p_due_date,
        v_current_due
    );

    IF v_effective_start IS NOT NULL
       AND v_effective_due IS NOT NULL
       AND v_effective_due < v_effective_start THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Due date cannot be before start date';
    END IF;

    IF p_status_supplied = 1
       AND NOT EXISTS (
            SELECT 1
            FROM task_statuses
            WHERE status_id = p_status_id
              AND is_active = 1
       ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Invalid task status';
    END IF;

    UPDATE tasks
    SET
        title = IF(p_title_supplied = 1, TRIM(p_title), title),
        description = IF(
            p_description_supplied = 1,
            NULLIF(TRIM(p_description), ''),
            description
        ),
        task_type_id = IF(
            p_task_type_supplied = 1,
            p_task_type_id,
            task_type_id
        ),
        priority_id = IF(
            p_priority_supplied = 1,
            p_priority_id,
            priority_id
        ),
        start_date = IF(
            p_start_date_supplied = 1,
            p_start_date,
            start_date
        ),
        due_date = IF(
            p_due_date_supplied = 1,
            p_due_date,
            due_date
        ),
        estimated_hours = IF(
            p_estimated_hours_supplied = 1,
            p_estimated_hours,
            estimated_hours
        ),
        status_id = IF(
            p_status_supplied = 1,
            p_status_id,
            status_id
        ),
        updated_at = UTC_TIMESTAMP(6)
    WHERE task_id = p_task_id;

    IF p_assignee_supplied = 1 THEN
        DELETE FROM task_assignees
        WHERE task_id = p_task_id
          AND user_id <> p_assignee_id;

        IF NOT EXISTS (
            SELECT 1
            FROM task_assignees
            WHERE task_id = p_task_id
              AND user_id = p_assignee_id
        ) THEN
            INSERT INTO task_assignees (
                task_id,
                user_id,
                assignment_role,
                assigned_by,
                assigned_at
            )
            VALUES (
                p_task_id,
                p_assignee_id,
                NULL,
                p_changed_by,
                UTC_TIMESTAMP(6)
            );
        END IF;
    END IF;

    SELECT p_task_id AS task_id;
END $$

DELIMITER ;
