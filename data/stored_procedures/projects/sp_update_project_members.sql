-- Update the complete membership set for a project.
-- The project creator must remain a member.
-- New members must belong to the same organisation and be active.
-- Existing inactive members may be retained or removed.

DROP PROCEDURE IF EXISTS sp_update_project_members;

DELIMITER $$

CREATE PROCEDURE sp_update_project_members(
    IN p_project_id BIGINT,
    IN p_organisation_id BIGINT,
    IN p_member_ids JSON
)
BEGIN
    DECLARE v_exists INT DEFAULT 0;
    DECLARE v_creator_id BIGINT;
    DECLARE v_member_count INT DEFAULT 0;
    DECLARE v_valid_member_count INT DEFAULT 0;

    SELECT COUNT(*), MAX(created_by)
      INTO v_exists, v_creator_id
    FROM projects
    WHERE project_id = p_project_id
      AND organisation_id = p_organisation_id;

    IF v_exists = 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Project not found';
    END IF;

    IF p_member_ids IS NULL
       OR JSON_TYPE(p_member_ids) <> 'ARRAY' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Project members must be an array';
    END IF;

    SELECT COUNT(DISTINCT member_data.user_id)
      INTO v_member_count
    FROM JSON_TABLE(
        p_member_ids,
        '$[*]' COLUMNS (
            user_id BIGINT PATH '$'
        )
    ) AS member_data;

    IF NOT EXISTS (
        SELECT 1
        FROM JSON_TABLE(
            p_member_ids,
            '$[*]' COLUMNS (
                user_id BIGINT PATH '$'
            )
        ) AS creator_data
        WHERE creator_data.user_id = v_creator_id
    ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Project creator must remain a member';
    END IF;

    SELECT COUNT(DISTINCT member_data.user_id)
      INTO v_valid_member_count
    FROM JSON_TABLE(
        p_member_ids,
        '$[*]' COLUMNS (
            user_id BIGINT PATH '$'
        )
    ) AS member_data
    INNER JOIN users u
        ON u.user_id = member_data.user_id
       AND u.organisation_id = p_organisation_id
    WHERE LOWER(u.status) = 'active'
       OR EXISTS (
            SELECT 1
            FROM project_members existing_member
            WHERE existing_member.project_id = p_project_id
              AND existing_member.user_id = u.user_id
       );

    IF v_valid_member_count <> v_member_count THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT =
                'One or more project members are invalid or inactive';
    END IF;

    DELETE FROM project_members
    WHERE project_id = p_project_id
      AND user_id NOT IN (
          SELECT selected_members.user_id
          FROM JSON_TABLE(
              p_member_ids,
              '$[*]' COLUMNS (
                  user_id BIGINT PATH '$'
              )
          ) AS selected_members
      );

    INSERT IGNORE INTO project_members (
        project_id,
        user_id,
        project_role,
        joined_at
    )
    SELECT
        p_project_id,
        selected_members.user_id,
        NULL,
        NOW()
    FROM JSON_TABLE(
        p_member_ids,
        '$[*]' COLUMNS (
            user_id BIGINT PATH '$'
        )
    ) AS selected_members
    INNER JOIN users u
        ON u.user_id = selected_members.user_id
       AND u.organisation_id = p_organisation_id
    WHERE LOWER(u.status) = 'active'
       OR EXISTS (
            SELECT 1
            FROM project_members existing_member
            WHERE existing_member.project_id = p_project_id
              AND existing_member.user_id = u.user_id
       );

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
