DROP PROCEDURE IF EXISTS sp_get_task_comments;

DELIMITER $$

CREATE PROCEDURE sp_get_task_comments(
    IN p_task_id BIGINT
)
BEGIN
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
    WHERE c.task_id = p_task_id
    ORDER BY c.created_at, c.comment_id;
END $$

DELIMITER ;
