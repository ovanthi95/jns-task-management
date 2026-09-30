-- API 11
-- Endpoint: GET /api/tasks/:taskId/audit

DROP PROCEDURE IF EXISTS sp_get_task_audit;

DELIMITER $$

CREATE PROCEDURE sp_get_task_audit(
    IN p_task_id BIGINT
)
BEGIN
    SELECT
        th.history_id,
        th.task_id,
        th.changed_by,
        u.first_name,
        u.last_name,
        th.field_name,
        th.old_value,
        th.new_value,
        th.changed_at
    FROM task_history th
    INNER JOIN users u
        ON u.user_id = th.changed_by
    WHERE th.task_id = p_task_id
    ORDER BY th.changed_at DESC, th.history_id DESC;
END $$

DELIMITER ;
