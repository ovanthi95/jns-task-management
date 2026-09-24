-- API 03 - User create
-- Owner: Manatka
-- Inserts one user into one organisation and returns the new row (same shape as sp_get_users).
-- p_password_hash must already be hashed by Django. A plain password must never reach this procedure.
-- Duplicate (organisation_id, email) raises MySQL 1062 and unknown role_id raises 1452;
-- both are mapped to 400 field errors in the Django service, not here.

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

    INSERT INTO users (
        organisation_id, role_id, first_name, last_name, email,
        password_hash, availability, status, created_at, updated_at
    )
    VALUES (
        p_organisation_id, p_role_id, p_first_name, p_last_name, p_email,
        p_password_hash, p_availability, 'Active', NOW(6), NOW(6)
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
        u.status
    FROM users u
    INNER JOIN roles r
        ON r.role_id = u.role_id
    WHERE u.user_id = v_user_id;
END $$

DELIMITER ;