-- API 09
-- Endpoint: POST /api/tasks/:taskId/comments

DROP PROCEDURE IF EXISTS sp_add_comment;

DELIMITER $$

CREATE PROCEDURE sp_add_comment(
    IN p_task_id BIGINT,
    IN p_user_id BIGINT,
    IN p_comment_text TEXT
)
BEGIN
    IF p_comment_text IS NULL OR TRIM(p_comment_text) = '' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Comment cannot be blank';
    END IF;

    INSERT INTO comments (
        task_id,
        user_id,
        comment_text,
        created_at,
        updated_at
    )
    VALUES (
        p_task_id,
        p_user_id,
        TRIM(p_comment_text),
        UTC_TIMESTAMP(6),
        UTC_TIMESTAMP(6)
    );

    SELECT
        c.comment_id,
        c.task_id,
        c.user_id,
        u.first_name,
        u.last_name,
        c.comment_text,
        c.created_at,
        c.updated_at
    FROM comments c
    INNER JOIN users u
        ON u.user_id = c.user_id
    WHERE c.comment_id = LAST_INSERT_ID();
END $$

DELIMITER ;
