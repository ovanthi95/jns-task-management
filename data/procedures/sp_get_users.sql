-- API 02  GET /api/users
-- Owner: Manatka
--
-- Returns every user in ONE organisation, with the role name joined so the
-- API can answer without a second query. The organisation id must come from
-- the authenticated session in Django, never from the request body.
--
-- password_hash is deliberately not selected.
--
-- Apply locally:
--   mysql -h 127.0.0.1 -u worklink_dev -p worklink < data/procedures/sp_get_users.sql

DROP PROCEDURE IF EXISTS sp_get_users;

DELIMITER $$

CREATE PROCEDURE sp_get_users(
    IN p_organisation_id INT
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
        u.status
    FROM users AS u
    INNER JOIN roles AS r
        ON r.role_id = u.role_id
    WHERE u.organisation_id = p_organisation_id
    ORDER BY u.last_name, u.first_name, u.user_id;
END$$

DELIMITER ;