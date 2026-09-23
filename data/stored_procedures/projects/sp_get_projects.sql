-- API 05 - Get Projects
-- Owner: Jessie
-- Endpoint: GET /api/projects
-- Stored procedure: sp_get_projects
--
-- Returns projects belonging to the authenticated user's organisation.

DROP PROCEDURE IF EXISTS sp_get_projects;

DELIMITER $$

CREATE PROCEDURE sp_get_projects(
    IN p_organisation_id INT
)
BEGIN

    SELECT
        p.project_id,
        p.organisation_id,
        p.project_name,
        p.description,
        p.status,
        p.start_date,
        p.end_date,
        p.created_by,
        p.created_at,
        p.updated_at
    FROM projects p
    WHERE p.organisation_id = p_organisation_id
    ORDER BY p.created_at DESC;

END $$

DELIMITER ;