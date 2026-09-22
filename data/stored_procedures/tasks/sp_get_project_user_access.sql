-- API 06 and API 07 (shared support procedure)
-- Owner: Edward
-- Endpoints: POST /api/projects/:projectId/tasks
--            GET  /api/projects/:projectId/tasks
-- Stored procedure: sp_get_project_user_access
--
-- Called by: application/django/data_access/tasks/get_project_user_access.py
--
-- Both task endpoints must answer two questions before touching any task row:
--   1. does this project exist, does it belong to the same organisation as the
--      person asking, and is that person a member of it?   -> 404 if not
--   2. for API 06 only, does the chosen assignee belong to the same
--      organisation and is that user a member of the project?  -> 400 if not
--
-- Both questions have the same shape, so one procedure answers both. The
-- caller passes its own user_id the first time and the assignee's user_id the
-- second time, and the service layer decides which status code to raise.
--
-- Two different outcomes are deliberately distinguishable:
--   * project missing        -> zero rows
--   * project found, no user -> one row with NULL user columns
-- The first means 404, the second means the submitted assignee_id is not a
-- real user, which is a 400. Collapsing them into "no rows" would lose that.
--
-- It lives in stored_procedures/tasks/ rather than stored_procedures/projects/
-- because it exists only to serve API 06 and API 07. The project endpoints
-- (API 04 and 05) are Jesse's and are not affected by this file.
--
-- Read only. No permission decision is made here; the procedure reports
-- facts and the service layer applies the rules.
--
-- Every column is listed explicitly. No SELECT *.
--
-- Safe to rerun. No DEFINER clause.

DROP PROCEDURE IF EXISTS sp_get_project_user_access;

DELIMITER $

CREATE PROCEDURE sp_get_project_user_access (
    IN p_project_id INT,
    IN p_user_id    INT
)
BEGIN
    SELECT
        p.project_id       AS project_id,
        p.organisation_id  AS project_organisation_id,
        u.user_id          AS user_id,
        u.organisation_id  AS user_organisation_id,
        EXISTS (
            SELECT 1
            FROM project_members pm
            WHERE pm.project_id = p.project_id
              AND pm.user_id    = p_user_id
        )                  AS is_member
    FROM projects p
    LEFT JOIN users u
           ON u.user_id = p_user_id
    WHERE p.project_id = p_project_id;
END$

DELIMITER ;
