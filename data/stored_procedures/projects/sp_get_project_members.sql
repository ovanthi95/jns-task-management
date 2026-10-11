-- Read current project members for the Edit Project flow.

DROP PROCEDURE IF EXISTS sp_get_project_members;

DELIMITER $$

CREATE PROCEDURE sp_get_project_members(
    IN p_project_id BIGINT,
    IN p_organisation_id BIGINT
)
BEGIN
    SELECT
        u.user_id,
        u.first_name,
        u.last_name,
        u.email,
        r.role_name,
        u.status,
        CASE
            WHEN u.user_id = p.created_by THEN 1
            ELSE 0
        END AS is_creator
    FROM projects p
    INNER JOIN project_members pm
        ON pm.project_id = p.project_id
    INNER JOIN users u
        ON u.user_id = pm.user_id
    LEFT JOIN roles r
        ON r.role_id = u.role_id
    WHERE p.project_id = p_project_id
      AND p.organisation_id = p_organisation_id
    ORDER BY u.first_name, u.last_name, u.user_id;
END $$

DELIMITER ;
