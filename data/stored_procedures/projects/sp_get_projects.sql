-- API 05 - Get Projects
-- Owner: Jessie
-- Endpoint: GET /api/projects

DROP PROCEDURE IF EXISTS sp_get_projects;

DELIMITER $$

CREATE PROCEDURE sp_get_projects(
    IN p_organisation_id BIGINT
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
        p.updated_at,
        COALESCE(
            SUM(CASE WHEN ts.status_name = 'Completed' THEN 1 ELSE 0 END),
            0
        ) AS completed_tasks,
        COUNT(t.task_id) AS total_tasks
    FROM projects p
    LEFT JOIN tasks t
        ON t.project_id = p.project_id
    LEFT JOIN task_statuses ts
        ON ts.status_id = t.status_id
    WHERE p.organisation_id = p_organisation_id
    GROUP BY
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
    ORDER BY
        CASE p.status
            WHEN 'Active' THEN 1
            WHEN 'Inactive' THEN 2
            WHEN 'Completed' THEN 3
            ELSE 4
        END,
        p.updated_at DESC,
        p.project_name ASC;
END $$

DELIMITER ;
