-- API 03 - User create
-- Owner: Manatka
-- Inserts one user into the authenticated user's organisation.

DROP PROCEDURE IF EXISTS sp_create_user;

DELIMITER $$

CREATE PROCEDURE sp_create_user(
    IN p_organisation_id INT,
    IN p_role_id         INT,
    IN p_first_name      VARCHAR(80),
    IN p_last_name       VARCHAR(80),
    IN p_email           VARCHAR(150),
    IN p_password_hash   VARCHAR(255),
    IN p_availability    VARCHAR(30)
)
BEGIN
    DECLARE v_user_id INT;
    DECLARE v_email VARCHAR(150);

    SET v_email = LOWER(TRIM(p_email));

    IF NOT EXISTS (
        SELECT 1
        FROM organisations
        WHERE organisation_id = p_organisation_id
          AND LOWER(status) = 'active'
    ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Invalid organisation';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM roles
        WHERE role_id = p_role_id
          AND is_active = 1
    ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Invalid role';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM users
        WHERE organisation_id = p_organisation_id
          AND LOWER(email) = v_email
    ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Email already exists';
    END IF;

    INSERT INTO users (
        organisation_id,
        role_id,
        first_name,
        last_name,
        email,
        password_hash,
        availability,
        status,
        created_at,
        updated_at
    )
    VALUES (
        p_organisation_id,
        p_role_id,
        TRIM(p_first_name),
        TRIM(p_last_name),
        v_email,
        p_password_hash,
        p_availability,
        'Active',
        NOW(6),
        NOW(6)
    );

    SET v_user_id = LAST_INSERT_ID();

    SELECT
        u.user_id,
        u.first_name,
        u.last_name,
        u.email,
        u.role_id,
        r.role_name,
        u.availability,
        u.status,
        u.created_at,
        u.updated_at
    FROM users u
    INNER JOIN roles r
        ON r.role_id = u.role_id
    WHERE u.user_id = v_user_id;
END $$

DELIMITER ;
