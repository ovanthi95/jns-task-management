DROP PROCEDURE IF EXISTS sp_update_project;

DELIMITER $$

CREATE PROCEDURE sp_update_project(
    IN p_project_id BIGINT,
    IN p_organisation_id BIGINT,
    IN p_project_name_supplied TINYINT,
    IN p_project_name VARCHAR(150),
    IN p_description_supplied TINYINT,
    IN p_description TEXT,
    IN p_start_date_supplied TINYINT,
    IN p_start_date DATE,
    IN p_end_date_supplied TINYINT,
    IN p_end_date DATE,
    IN p_status_supplied TINYINT,
    IN p_status VARCHAR(30)
)
BEGIN
    DECLARE v_exists INT DEFAULT 0;
    DECLARE v_current_start DATE;
    DECLARE v_current_end DATE;
    DECLARE v_effective_start DATE;
    DECLARE v_effective_end DATE;

    SELECT COUNT(*), MAX(start_date), MAX(end_date)
      INTO v_exists, v_current_start, v_current_end
    FROM projects
    WHERE project_id = p_project_id
      AND organisation_id = p_organisation_id;

    IF v_exists = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Project not found';
    END IF;

    IF p_project_name_supplied = 1
       AND (p_project_name IS NULL OR TRIM(p_project_name) = '') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Project name is required';
    END IF;

    IF p_status_supplied = 1
       AND p_status NOT IN ('Active', 'Inactive', 'Completed') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid project status';
    END IF;

    SET v_effective_start = IF(p_start_date_supplied = 1, p_start_date, v_current_start);
    SET v_effective_end = IF(p_end_date_supplied = 1, p_end_date, v_current_end);

    IF v_effective_start IS NOT NULL
       AND v_effective_end IS NOT NULL
       AND v_effective_end < v_effective_start THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'End date cannot be before start date';
    END IF;

    UPDATE projects
    SET
        project_name = IF(p_project_name_supplied = 1, TRIM(p_project_name), project_name),
        description = IF(p_description_supplied = 1, NULLIF(TRIM(p_description), ''), description),
        start_date = IF(p_start_date_supplied = 1, p_start_date, start_date),
        end_date = IF(p_end_date_supplied = 1, p_end_date, end_date),
        status = IF(p_status_supplied = 1, p_status, status),
        updated_at = NOW()
    WHERE project_id = p_project_id
      AND organisation_id = p_organisation_id;

    SELECT
        p.project_id, p.project_name, p.description, p.status,
        p.start_date, p.end_date, p.created_at, p.updated_at,
        COALESCE(SUM(CASE WHEN ts.status_name = 'Completed' THEN 1 ELSE 0 END), 0) AS completed_tasks,
        COUNT(t.task_id) AS total_tasks
    FROM projects p
    LEFT JOIN tasks t ON t.project_id = p.project_id
    LEFT JOIN task_statuses ts ON ts.status_id = t.status_id
    WHERE p.project_id = p_project_id
      AND p.organisation_id = p_organisation_id
    GROUP BY
        p.project_id, p.project_name, p.description, p.status,
        p.start_date, p.end_date, p.created_at, p.updated_at;
END$$

DELIMITER ;
