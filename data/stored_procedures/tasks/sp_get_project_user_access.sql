-- API 06 and API 07 shared project/user access facts.

DROP PROCEDURE IF EXISTS sp_get_project_user_access;

DELIMITER $

CREATE PROCEDURE sp_get_project_user_access (
    IN p_project_id INT,
    IN p_user_id    INT
)
BEGIN
    SELECT
        p.project_id          AS project_id,
        p.project_name        AS project_name,
        p.status              AS project_status,
        p.organisation_id     AS project_organisation_id,
        u.user_id             AS user_id,
        u.organisation_id     AS user_organisation_id,
        EXISTS (
            SELECT 1
            FROM project_members pm
            WHERE pm.project_id = p.project_id
              AND pm.user_id = p_user_id
        ) AS is_member
    FROM projects p
    LEFT JOIN users u
        ON u.user_id = p_user_id
    WHERE p.project_id = p_project_id;
END$

DELIMITER ;
