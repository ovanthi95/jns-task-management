-- Auth session check
-- Owner: Ovanthi
-- Returns the currently authenticated active JNS user by user_id.

DROP PROCEDURE IF EXISTS sp_get_session_user;

DELIMITER $$

CREATE PROCEDURE sp_get_session_user(
    IN p_user_id INT
)
BEGIN
    SELECT
        u.user_id,
        u.first_name,
        u.last_name,
        u.email,
        u.status,
        u.organisation_id,
        u.role_id,
        r.role_name,
        o.organisation_name
    FROM users u
    INNER JOIN roles r
        ON r.role_id = u.role_id
    INNER JOIN organisations o
        ON o.organisation_id = u.organisation_id
    WHERE u.user_id = p_user_id
      AND LOWER(u.status) = 'active'
      AND LOWER(o.status) = 'active'
      AND LOWER(o.organisation_name) = 'jns business solutions'
    LIMIT 1;
END $$

DELIMITER ;