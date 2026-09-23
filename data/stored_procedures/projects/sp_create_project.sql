-- API 04 - Create Project
-- Owner: Jessie
-- Endpoint: POST /api/projects
-- Stored procedure: sp_create_project
--
-- Creates a project and its project memberships atomically.
-- Member IDs are supplied as a JSON array, for example: [2, 5, 8].

DROP PROCEDURE IF EXISTS sp_create_project;

DELIMITER $$

CREATE PROCEDURE sp_create_project(
    IN p_organisation_id INT,
    IN p_project_name VARCHAR(150),
    IN p_description TEXT,
    IN p_start_date DATE,
    IN p_end_date DATE,
    IN p_created_by INT,
    IN p_member_ids JSON
)
BEGIN
    DECLARE v_project_id INT;
    DECLARE v_member_count INT DEFAULT 0;
    DECLARE v_valid_member_count INT DEFAULT 0;

    -- Roll back the whole operation if any SQL error occurs.
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    -- Validate project members.
    -- Every member must:
    -- 1. exist,
    -- 2. belong to the same organisation,
    -- 3. have Active status.
    IF p_member_ids IS NOT NULL
       AND JSON_LENGTH(p_member_ids) > 0 THEN

        SET v_member_count = JSON_LENGTH(p_member_ids);

        SELECT COUNT(*)
        INTO v_valid_member_count
        FROM users u
        INNER JOIN JSON_TABLE(
            p_member_ids,
            '$[*]' COLUMNS (
                user_id INT PATH '$'
            )
        ) AS member_data
            ON member_data.user_id = u.user_id
        WHERE u.organisation_id = p_organisation_id
          AND LOWER(u.status) = 'active';

        IF v_valid_member_count <> v_member_count THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT =
                    'One or more project members are invalid or inactive.';
        END IF;

    END IF;

    -- Create the project.
    INSERT INTO projects (
        organisation_id,
        project_name,
        description,
        status,
        start_date,
        end_date,
        created_by,
        created_at,
        updated_at
    )
    VALUES (
        p_organisation_id,
        p_project_name,
        p_description,
        'Active',
        p_start_date,
        p_end_date,
        p_created_by,
        NOW(),
        NOW()
    );

    SET v_project_id = LAST_INSERT_ID();

    -- Create project memberships.
    IF p_member_ids IS NOT NULL
       AND JSON_LENGTH(p_member_ids) > 0 THEN

        INSERT INTO project_members (
            project_id,
            user_id,
            project_role,
            joined_at
        )
        SELECT
            v_project_id,
            member_data.user_id,
            NULL,
            NOW()
        FROM JSON_TABLE(
            p_member_ids,
            '$[*]' COLUMNS (
                user_id INT PATH '$'
            )
        ) AS member_data;

    END IF;

    COMMIT;

    -- Return the newly created project.
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
    WHERE p.project_id = v_project_id;

END $$

DELIMITER ;