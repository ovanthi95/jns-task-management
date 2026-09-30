-- API 12
-- Endpoint: PATCH /api/users/:userId

DROP PROCEDURE IF EXISTS sp_update_user;

DELIMITER $$

CREATE PROCEDURE sp_update_user(
    IN p_user_id BIGINT,
    IN p_organisation_id BIGINT,
    IN p_first_name_supplied TINYINT,
    IN p_first_name VARCHAR(80),
    IN p_last_name_supplied TINYINT,
    IN p_last_name VARCHAR(80),
    IN p_email_supplied TINYINT,
    IN p_email VARCHAR(150),
    IN p_role_supplied TINYINT,
    IN p_role_id BIGINT,
    IN p_availability_supplied TINYINT,
    IN p_availability VARCHAR(30),
    IN p_status_supplied TINYINT,
    IN p_status VARCHAR(20)
)
BEGIN
    DECLARE v_exists INT DEFAULT 0;
    DECLARE v_email VARCHAR(150);

    SELECT COUNT(*)
      INTO v_exists
    FROM users
    WHERE user_id = p_user_id
      AND organisation_id = p_organisation_id;

    IF v_exists = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'User not found';
    END IF;

    IF p_first_name_supplied = 1
       AND (p_first_name IS NULL OR TRIM(p_first_name) = '') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'First name is required';
    END IF;

    IF p_last_name_supplied = 1
       AND (p_last_name IS NULL OR TRIM(p_last_name) = '') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Last name is required';
    END IF;

    IF p_email_supplied = 1 THEN
        SET v_email = LOWER(TRIM(p_email));

        IF v_email IS NULL OR v_email = '' THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Email is required';
        END IF;

        IF EXISTS (
            SELECT 1
            FROM users
            WHERE organisation_id = p_organisation_id
              AND LOWER(email) = v_email
              AND user_id <> p_user_id
        ) THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Email already exists';
        END IF;
    END IF;

    IF p_role_supplied = 1
       AND NOT EXISTS (
            SELECT 1
            FROM roles
            WHERE role_id = p_role_id
              AND is_active = 1
       ) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid role';
    END IF;

    IF p_status_supplied = 1
       AND p_status NOT IN ('Active', 'Inactive') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid user status';
    END IF;

    UPDATE users
    SET
        first_name = IF(
            p_first_name_supplied = 1,
            TRIM(p_first_name),
            first_name
        ),
        last_name = IF(
            p_last_name_supplied = 1,
            TRIM(p_last_name),
            last_name
        ),
        email = IF(p_email_supplied = 1, v_email, email),
        role_id = IF(p_role_supplied = 1, p_role_id, role_id),
        availability = IF(
            p_availability_supplied = 1,
            NULLIF(TRIM(p_availability), ''),
            availability
        ),
        status = IF(p_status_supplied = 1, p_status, status),
        updated_at = NOW()
    WHERE user_id = p_user_id
      AND organisation_id = p_organisation_id;

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
    WHERE u.user_id = p_user_id
      AND u.organisation_id = p_organisation_id;
END $$

DELIMITER ;
