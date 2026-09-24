-- API 06
-- Owner: Edward
-- Endpoint: POST /api/projects/:projectId/tasks
-- Stored procedure: sp_create_task
--
-- Called by: application/django/data_access/tasks/create_task.py
--
-- Creates one task and its first assignment.
--
-- Transactions are NOT controlled here. The Django service layer opens the
-- transaction (transaction.atomic) so that the task row and the assignee row
-- are committed together. Opening a transaction inside a procedure would
-- implicitly commit the caller's transaction and allow orphan tasks.
--
-- This procedure performs no permission checks and no organisation checks.
-- Those belong to the service layer, which resolves them from the session
-- before calling this procedure.
--
-- created_at / updated_at / assigned_at are set explicitly because a direct
-- INSERT does not go through Django's auto_now_add / auto_now. Django runs
-- with USE_TZ = True and TIME_ZONE = 'UTC', so UTC_TIMESTAMP is the value
-- Django would have written.
--
-- Safe to rerun. No DEFINER clause.

DROP PROCEDURE IF EXISTS sp_create_task;

DELIMITER $

CREATE PROCEDURE sp_create_task (
    IN p_project_id        INT,
    IN p_task_type_id      INT,
    IN p_status_id         INT,
    IN p_priority_id       INT,
    IN p_title             VARCHAR(200),
    IN p_description       TEXT,
    IN p_start_date        DATE,
    IN p_due_date          DATE,
    IN p_estimated_hours   DECIMAL(6,2),
    IN p_assignee_user_id  INT,
    IN p_created_by        INT
)
BEGIN
    DECLARE v_task_id INT;
    DECLARE v_now DATETIME(6);

    SET v_now = UTC_TIMESTAMP(6);

    INSERT INTO tasks (
        project_id,
        task_type_id,
        status_id,
        priority_id,
        title,
        description,
        start_date,
        due_date,
        estimated_hours,
        actual_hours,
        created_by,
        created_at,
        updated_at
    ) VALUES (
        p_project_id,
        p_task_type_id,
        p_status_id,
        p_priority_id,
        p_title,
        p_description,
        p_start_date,
        p_due_date,
        p_estimated_hours,
        NULL,
        p_created_by,
        v_now,
        v_now
    );

    SET v_task_id = LAST_INSERT_ID();

    -- assignment_role stays NULL: API 06 does not accept it.
    INSERT INTO task_assignees (
        task_id,
        user_id,
        assignment_role,
        assigned_by,
        assigned_at
    ) VALUES (
        v_task_id,
        p_assignee_user_id,
        NULL,
        p_created_by,
        v_now
    );

    SELECT v_task_id AS task_id;
END$

DELIMITER ;
