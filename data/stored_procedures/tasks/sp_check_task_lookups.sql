-- API 06 (support procedure)
-- Owner: Edward
-- Endpoint: POST /api/projects/:projectId/tasks
-- Stored procedure: sp_check_task_lookups
--
-- Called by: application/django/data_access/tasks/check_task_lookups.py
--
-- task_type_id, status_id and priority_id are NOT NULL foreign keys with no
-- default. A body naming an id that does not exist has to come back as 400
-- with the offending field named. Letting it reach the INSERT instead would
-- surface as a foreign-key error and a 500.
--
-- All three are answered in one round trip, and all three are answered even
-- when the first one already failed, so the client sees every bad field at
-- once instead of one per request.
--
-- Read only. Reports existence; the service decides what to do about it.
--
-- Safe to rerun. No DEFINER clause.

DROP PROCEDURE IF EXISTS sp_check_task_lookups;

DELIMITER $

CREATE PROCEDURE sp_check_task_lookups (
    IN p_task_type_id INT,
    IN p_status_id    INT,
    IN p_priority_id  INT
)
BEGIN
    SELECT
        EXISTS (
            SELECT 1 FROM task_types
            WHERE task_type_id = p_task_type_id
        ) AS task_type_exists,
        EXISTS (
            SELECT 1 FROM task_statuses
            WHERE status_id = p_status_id
        ) AS status_exists,
        EXISTS (
            SELECT 1 FROM priorities
            WHERE priority_id = p_priority_id
        ) AS priority_exists;
END$

DELIMITER ;
