-- API 02 - Users list
-- Owner: Manatka
-- Returns all users in one organisation with role name joined.
-- password_hash is never selected. organisation_id comes from the session user in Django.

DROP PROCEDURE IF EXISTS sp_get_users;

DELIMITER $$

CREATE PROCEDURE sp_get_users(
    IN p_organisation_id BIGINT
)
BEGIN
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
    WHERE u.organisation_id = p_organisation_id
    ORDER BY
        CASE LOWER(u.status)
            WHEN 'active' THEN 1
            WHEN 'inactive' THEN 2
            ELSE 3
        END,
        u.first_name,
        u.last_name,
        u.user_id;
END $$

DELIMITER ;
