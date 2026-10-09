-- API 08
-- Owner: Ovanthi
-- Endpoint: PATCH /api/tasks/:taskId
--
-- Partial task update. The service layer decides who may update which fields.
-- This procedure defensively validates all supplied ids and writes task_history
-- rows only when a value actually changes.

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
    IN p_other_task_type_supplied TINYINT,
    IN p_other_task_type VARCHAR(100),

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

    DECLARE v_old_title VARCHAR(200);
    DECLARE v_old_description TEXT;

    DECLARE v_old_task_type_id INT;
    DECLARE v_old_task_type_name VARCHAR(50);
    DECLARE v_new_task_type_name VARCHAR(50);
    DECLARE v_old_other_task_type VARCHAR(100);
    DECLARE v_new_other_task_type VARCHAR(100);

    DECLARE v_old_priority_id INT;
    DECLARE v_old_priority_name VARCHAR(30);
    DECLARE v_new_priority_name VARCHAR(30);

    DECLARE v_old_assignee_id INT;
    DECLARE v_old_assignee_name VARCHAR(170);
    DECLARE v_new_assignee_name VARCHAR(170);

    DECLARE v_old_start_date DATE;
    DECLARE v_old_due_date DATE;
    DECLARE v_effective_start_date DATE;
    DECLARE v_effective_due_date DATE;

    DECLARE v_old_estimated_hours DECIMAL(6,2);

    DECLARE v_old_status_id INT;
    DECLARE v_old_status_name VARCHAR(50);
    DECLARE v_new_status_name VARCHAR(50);

    SELECT
        t.project_id,
        t.title,
        t.description,
        t.task_type_id,
        tt.type_name,
        t.other_task_type,
        t.priority_id,
        pr.priority_name,
        t.start_date,
        t.due_date,
        t.estimated_hours,
        t.status_id,
        ts.status_name
    INTO
        v_project_id,
        v_old_title,
        v_old_description,
        v_old_task_type_id,
        v_old_task_type_name,
        v_old_other_task_type,
        v_old_priority_id,
        v_old_priority_name,
        v_old_start_date,
        v_old_due_date,
        v_old_estimated_hours,
        v_old_status_id,
        v_old_status_name
    FROM tasks t
    INNER JOIN projects p
        ON p.project_id = t.project_id
    INNER JOIN task_types tt
        ON tt.task_type_id = t.task_type_id
    INNER JOIN priorities pr
        ON pr.priority_id = t.priority_id
    INNER JOIN task_statuses ts
        ON ts.status_id = t.status_id
    WHERE t.task_id = p_task_id
      AND p.organisation_id = p_organisation_id
    LIMIT 1;

    IF v_project_id IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Task not found';
    END IF;

    SELECT
        ta.user_id,
        TRIM(CONCAT(u.first_name, ' ', u.last_name))
    INTO
        v_old_assignee_id,
        v_old_assignee_name
    FROM task_assignees ta
    INNER JOIN users u
        ON u.user_id = ta.user_id
    WHERE ta.task_id = p_task_id
    ORDER BY ta.assigned_at, ta.task_assignee_id
    LIMIT 1;

    IF p_title_supplied = 1
       AND (p_title IS NULL OR TRIM(p_title) = '') THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Task title is required';
    END IF;

    IF p_task_type_supplied = 1 THEN
        SELECT type_name
        INTO v_new_task_type_name
        FROM task_types
        WHERE task_type_id = p_task_type_id
          AND is_active = 1
        LIMIT 1;

        IF v_new_task_type_name IS NULL THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Invalid task type';
        END IF;
    ELSE
        SET v_new_task_type_name = v_old_task_type_name;
    END IF;

    SET v_new_other_task_type = v_old_other_task_type;

    IF LOWER(v_new_task_type_name) = 'other' THEN
        IF p_other_task_type_supplied = 1 THEN
            IF p_other_task_type IS NULL OR TRIM(p_other_task_type) = '' THEN
                SIGNAL SQLSTATE '45000'
                    SET MESSAGE_TEXT = 'Other task type is required';
            END IF;
            SET v_new_other_task_type = TRIM(p_other_task_type);
        ELSEIF v_old_other_task_type IS NULL OR TRIM(v_old_other_task_type) = '' THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Other task type is required';
        END IF;
    ELSE
        SET v_new_other_task_type = NULL;
    END IF;

    IF p_priority_supplied = 1 THEN
        SELECT priority_name
        INTO v_new_priority_name
        FROM priorities
        WHERE priority_id = p_priority_id
          AND is_active = 1
        LIMIT 1;

        IF v_new_priority_name IS NULL THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Invalid priority';
        END IF;
    END IF;

    IF p_assignee_supplied = 1 THEN
        SELECT TRIM(CONCAT(u.first_name, ' ', u.last_name))
        INTO v_new_assignee_name
        FROM users u
        INNER JOIN project_members pm
            ON pm.user_id = u.user_id
           AND pm.project_id = v_project_id
        WHERE u.user_id = p_assignee_id
          AND u.organisation_id = p_organisation_id
          AND LOWER(u.status) = 'active'
        LIMIT 1;

        IF v_new_assignee_name IS NULL THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Invalid assignee';
        END IF;
    END IF;

    IF p_estimated_hours_supplied = 1
       AND p_estimated_hours IS NOT NULL
       AND p_estimated_hours < 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Invalid estimated hours';
    END IF;

    SET v_effective_start_date = IF(
        p_start_date_supplied = 1,
        p_start_date,
        v_old_start_date
    );

    SET v_effective_due_date = IF(
        p_due_date_supplied = 1,
        p_due_date,
        v_old_due_date
    );

    IF v_effective_start_date IS NOT NULL
       AND v_effective_due_date IS NOT NULL
       AND v_effective_due_date < v_effective_start_date THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Due date cannot be before start date';
    END IF;

    IF p_status_supplied = 1 THEN
        SELECT status_name
        INTO v_new_status_name
        FROM task_statuses
        WHERE status_id = p_status_id
          AND is_active = 1
        LIMIT 1;

        IF v_new_status_name IS NULL THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Invalid task status';
        END IF;
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
        other_task_type = v_new_other_task_type,
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
        updated_at = NOW()
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
                NOW()
            );
        END IF;
    END IF;

    IF p_title_supplied = 1
       AND NOT (v_old_title <=> TRIM(p_title)) THEN
        INSERT INTO task_history (
            task_id, changed_by, field_name, old_value, new_value, changed_at
        )
        VALUES (
            p_task_id,
            p_changed_by,
            'title',
            JSON_OBJECT('value', v_old_title),
            JSON_OBJECT('value', TRIM(p_title)),
            NOW()
        );
    END IF;

    IF p_description_supplied = 1
       AND NOT (
            v_old_description <=>
            NULLIF(TRIM(p_description), '')
       ) THEN
        INSERT INTO task_history (
            task_id, changed_by, field_name, old_value, new_value, changed_at
        )
        VALUES (
            p_task_id,
            p_changed_by,
            'description',
            JSON_OBJECT('value', v_old_description),
            JSON_OBJECT('value', NULLIF(TRIM(p_description), '')),
            NOW()
        );
    END IF;

    IF p_task_type_supplied = 1
       AND NOT (v_old_task_type_id <=> p_task_type_id) THEN
        INSERT INTO task_history (
            task_id, changed_by, field_name, old_value, new_value, changed_at
        )
        VALUES (
            p_task_id,
            p_changed_by,
            'task_type_id',
            JSON_OBJECT(
                'task_type_id', v_old_task_type_id,
                'task_type_name', v_old_task_type_name
            ),
            JSON_OBJECT(
                'task_type_id', p_task_type_id,
                'task_type_name', v_new_task_type_name
            ),
            NOW()
        );
    END IF;

    IF NOT (v_old_other_task_type <=> v_new_other_task_type) THEN
        INSERT INTO task_history (
            task_id, changed_by, field_name, old_value, new_value, changed_at
        )
        VALUES (
            p_task_id,
            p_changed_by,
            'other_task_type',
            JSON_OBJECT('value', v_old_other_task_type),
            JSON_OBJECT('value', v_new_other_task_type),
            NOW()
        );
    END IF;

    IF p_priority_supplied = 1
       AND NOT (v_old_priority_id <=> p_priority_id) THEN
        INSERT INTO task_history (
            task_id, changed_by, field_name, old_value, new_value, changed_at
        )
        VALUES (
            p_task_id,
            p_changed_by,
            'priority_id',
            JSON_OBJECT(
                'priority_id', v_old_priority_id,
                'priority_name', v_old_priority_name
            ),
            JSON_OBJECT(
                'priority_id', p_priority_id,
                'priority_name', v_new_priority_name
            ),
            NOW()
        );
    END IF;

    IF p_assignee_supplied = 1
       AND NOT (v_old_assignee_id <=> p_assignee_id) THEN
        INSERT INTO task_history (
            task_id, changed_by, field_name, old_value, new_value, changed_at
        )
        VALUES (
            p_task_id,
            p_changed_by,
            'assignee_id',
            JSON_OBJECT(
                'user_id', v_old_assignee_id,
                'name', v_old_assignee_name
            ),
            JSON_OBJECT(
                'user_id', p_assignee_id,
                'name', v_new_assignee_name
            ),
            NOW()
        );
    END IF;

    IF p_start_date_supplied = 1
       AND NOT (v_old_start_date <=> p_start_date) THEN
        INSERT INTO task_history (
            task_id, changed_by, field_name, old_value, new_value, changed_at
        )
        VALUES (
            p_task_id,
            p_changed_by,
            'start_date',
            JSON_OBJECT('value', v_old_start_date),
            JSON_OBJECT('value', p_start_date),
            NOW()
        );
    END IF;

    IF p_due_date_supplied = 1
       AND NOT (v_old_due_date <=> p_due_date) THEN
        INSERT INTO task_history (
            task_id, changed_by, field_name, old_value, new_value, changed_at
        )
        VALUES (
            p_task_id,
            p_changed_by,
            'due_date',
            JSON_OBJECT('value', v_old_due_date),
            JSON_OBJECT('value', p_due_date),
            NOW()
        );
    END IF;

    IF p_estimated_hours_supplied = 1
       AND NOT (v_old_estimated_hours <=> p_estimated_hours) THEN
        INSERT INTO task_history (
            task_id, changed_by, field_name, old_value, new_value, changed_at
        )
        VALUES (
            p_task_id,
            p_changed_by,
            'estimated_hours',
            JSON_OBJECT('value', v_old_estimated_hours),
            JSON_OBJECT('value', p_estimated_hours),
            NOW()
        );
    END IF;

    IF p_status_supplied = 1
       AND NOT (v_old_status_id <=> p_status_id) THEN
        INSERT INTO task_history (
            task_id, changed_by, field_name, old_value, new_value, changed_at
        )
        VALUES (
            p_task_id,
            p_changed_by,
            'status_id',
            JSON_OBJECT(
                'status_id', v_old_status_id,
                'status_name', v_old_status_name
            ),
            JSON_OBJECT(
                'status_id', p_status_id,
                'status_name', v_new_status_name
            ),
            NOW()
        );
    END IF;

    SELECT p_task_id AS task_id;
END $$

DELIMITER ;
