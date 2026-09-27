-- API 08 support procedure

DROP PROCEDURE IF EXISTS sp_get_task_status;

DELIMITER $$

CREATE PROCEDURE sp_get_task_status(
    IN p_status_id INT
)
BEGIN
    SELECT
        status_id,
        status_name,
        is_terminal
    FROM task_statuses
    WHERE status_id = p_status_id
      AND is_active = 1
    LIMIT 1;
END $$

DELIMITER ;
