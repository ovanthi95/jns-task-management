-- API 10 - Add file metadata
-- Owner: Manatka
-- Inserts one attachments row after the file is already in S3 and returns it.
-- Access has already been checked by sp_get_task_access; uploaded_by comes from
-- the session user in Django, never from the request.

DROP PROCEDURE IF EXISTS sp_add_file;

DELIMITER $$

CREATE PROCEDURE sp_add_file(
    IN p_task_id     INT,
    IN p_uploaded_by INT,
    IN p_file_name   VARCHAR(255),
    IN p_file_type   VARCHAR(100),
    IN p_file_size   BIGINT UNSIGNED,
    IN p_s3_key      VARCHAR(500)
)
BEGIN
    DECLARE v_attachment_id INT;

    INSERT INTO attachments (
        task_id, uploaded_by, file_name, file_type, file_size, s3_key, uploaded_at
    )
    VALUES (
        p_task_id, p_uploaded_by, p_file_name, p_file_type, p_file_size, p_s3_key, NOW(6)
    );

    SET v_attachment_id = LAST_INSERT_ID();

    SELECT
        a.attachment_id,
        a.task_id,
        a.file_name,
        a.file_type,
        a.file_size,
        a.s3_key,
        a.uploaded_by,
        a.uploaded_at
    FROM attachments a
    WHERE a.attachment_id = v_attachment_id;
END $$

DELIMITER ;