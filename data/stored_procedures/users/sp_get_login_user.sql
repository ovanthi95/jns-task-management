-- API 01 - Login
-- Owner: Ovanthi
-- Retrieves an active JNS user by email.
-- Password verification is performed in Django, not in MySQL.

DROP PROCEDURE IF EXISTS sp_get_login_user;

DELIMITER $$

CREATE PROCEDURE sp_get_login_user(
    IN p_email VARCHAR(150)
)
BEGIN
    SELECT
        u.user_id,
        u.first_name,
        u.last_name,
        u.email,
        u.password_hash,
        u.status,
        u.organisation_id,
        u.role_id,
        r.role_name,
        o.organisation_name
    FROM users u
    INNER JOIN organisations o
        ON o.organisation_id = u.organisation_id
    INNER JOIN roles r
        ON r.role_id = u.role_id
    WHERE LOWER(u.email) = LOWER(TRIM(p_email))
      AND LOWER(u.status) = 'active'
      AND LOWER(o.status) = 'active'
      AND LOWER(o.organisation_name) = 'jns business solutions'
    LIMIT 1;
END $$

DELIMITER ;