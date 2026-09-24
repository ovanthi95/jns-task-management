-- API 10 - Task access check for file upload
-- Owner: Manatka
-- Returns the task only if it belongs to a project in the caller's organisation
-- AND the caller holds an explicit project_members row. Empty result means 404,
-- so an outsider cannot tell whether the task exists (same rule as API 06/07).

DROP PROCEDURE IF EXISTS sp_get_task_access;

DELIMITER $$

CREATE PROCEDURE sp_get_task_access(
    IN p_task_id INT,
    IN p_user_id INT
)
BEGIN
    SELECT
        t.task_id,
        t.project_id,
        p.organisation_id
    FROM tasks t
    INNER JOIN projects p
        ON p.project_id = t.project_id
    INNER JOIN users u
        ON u.user_id = p_user_id
       AND u.organisation_id = p.organisation_id
    INNER JOIN project_members pm
        ON pm.project_id = p.project_id
       AND pm.user_id = p_user_id
    WHERE t.task_id = p_task_id
    LIMIT 1;
END $$

DELIMITER ;