-- API 05 - Get Projects
-- Owner: Jessie

DROP PROCEDURE IF EXISTS sp_get_projects;

DELIMITER $$

CREATE PROCEDURE sp_get_projects(
    IN p_organisation_id INT,
    IN p_user_id INT,
    IN p_view_all TINYINT
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
        COALESCE(SUM(CASE WHEN ts.status_name = 'Completed' THEN 1 ELSE 0 END), 0) AS completed_tasks,
        COUNT(DISTINCT t.task_id) AS total_tasks
    FROM projects p
    LEFT JOIN tasks t
        ON t.project_id = p.project_id
    LEFT JOIN task_statuses ts
        ON ts.status_id = t.status_id
    WHERE p.organisation_id = p_organisation_id
      AND (
          p_view_all = 1
          OR EXISTS (
              SELECT 1
              FROM project_members pm
              WHERE pm.project_id = p.project_id
                AND pm.user_id = p_user_id
          )
      )
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
        p.project_name;
END $$

DELIMITER ;
