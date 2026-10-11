DROP PROCEDURE IF EXISTS sp_get_task_files;

DELIMITER $$

CREATE PROCEDURE sp_get_task_files(
    IN p_task_id BIGINT
)
BEGIN
    SELECT
        a.attachment_id,
        a.task_id,
        a.file_name,
        a.file_type,
        a.file_size,
        a.s3_key,
        a.uploaded_by,
        CONCAT_WS(' ', u.first_name, u.last_name) AS uploaded_by_name,
        a.uploaded_at
    FROM attachments a
    INNER JOIN users u
        ON u.user_id = a.uploaded_by
    WHERE a.task_id = p_task_id
    ORDER BY a.uploaded_at, a.attachment_id;
END $$

DELIMITER ;
