-- API 07
-- Owner: Edward
-- Endpoint: GET /api/projects/:projectId/tasks
-- Stored procedure: sp_get_project_tasks
--
-- Called by: application/django/data_access/tasks/get_project_tasks.py
--
-- Returns one relational row per task-assignee pair. Tasks with no assignee
-- still return one row because the assignee joins are LEFT JOINs.
--
-- The data-access layer groups repeated task rows into one task object and
-- builds the assignees list for the API response.
--
-- The optional filters are passed as NULL when absent. They AND together,
-- which is how the endpoint behaved before the refactor.
--
-- p_task_id is the one filter the client cannot reach. API 06 uses it to read
-- back the task it has just created, so the 201 body and the 200 rows are
-- produced by this single query and cannot drift apart.
--
-- This procedure performs no permission checks and no organisation checks.
-- The service layer has already proved that the caller may see this project
-- before it calls here.
--
-- p_assignee_id filters which tasks qualify, but the result still includes
-- every assignee on each matching task.
--
-- Every column is listed explicitly. No SELECT *.
--
-- Safe to rerun. No DEFINER clause.

DROP PROCEDURE IF EXISTS sp_get_project_tasks;

DELIMITER $$

CREATE PROCEDURE sp_get_project_tasks (
    IN p_project_id  INT,
    IN p_status_id   INT,
    IN p_priority_id INT,
    IN p_assignee_id INT,
    IN p_task_id     INT
)
BEGIN
    SELECT
        t.task_id                AS task_id,
        t.project_id             AS project_id,
        t.task_type_id           AS task_type_id,
        tt.type_name             AS task_type_name,
        t.status_id              AS status_id,
        ts.status_name           AS status_name,
        t.priority_id            AS priority_id,
        pr.priority_name         AS priority_name,
        t.title                  AS title,
        t.description            AS description,
        t.start_date             AS start_date,
        t.due_date               AS due_date,
        t.estimated_hours        AS estimated_hours,
        t.actual_hours           AS actual_hours,
        t.created_by             AS created_by_id,
        t.created_at             AS created_at,
        t.updated_at             AS updated_at,
        ta.user_id               AS assignee_user_id,
        u.first_name             AS assignee_first_name,
        u.last_name              AS assignee_last_name,
        ta.assignment_role       AS assignee_assignment_role,
        ta.task_assignee_id      AS task_assignee_id
    FROM tasks t
    INNER JOIN task_types    tt ON tt.task_type_id = t.task_type_id
    INNER JOIN task_statuses ts ON ts.status_id    = t.status_id
    INNER JOIN priorities    pr ON pr.priority_id  = t.priority_id
    LEFT JOIN task_assignees ta ON ta.task_id      = t.task_id
    LEFT JOIN users           u ON u.user_id        = ta.user_id
    WHERE t.project_id = p_project_id
      AND (p_task_id     IS NULL OR t.task_id     = p_task_id)
      AND (p_status_id   IS NULL OR t.status_id   = p_status_id)
      AND (p_priority_id IS NULL OR t.priority_id = p_priority_id)
      AND (
            p_assignee_id IS NULL
            OR EXISTS (
                SELECT 1
                FROM task_assignees f
                WHERE f.task_id = t.task_id
                  AND f.user_id = p_assignee_id
            )
          )
    ORDER BY
        t.created_at DESC,
        t.task_id DESC,
        ta.task_assignee_id ASC;
END$$

DELIMITER ;
