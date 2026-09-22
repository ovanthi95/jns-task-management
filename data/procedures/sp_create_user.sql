-- API 03  POST /api/users
-- Owner: Manatka
--
-- Inserts one user into ONE organisation and returns the new row in the same
-- shape as sp_get_users, so the API can answer 201 without a second query.
--
-- Rules:
--   * p_organisation_id comes from the authenticated session in Django,
--     never from the request body.
--   * p_password_hash must already be hashed by Django (make_password).
--     A plain password must never reach this procedure.
--   * Duplicate email in the organisation is NOT checked here. The unique
--     index (organisation_id, email) raises MySQL error 1062, which Django
--     turns into a 400. Doing it here would add a race between check and
--     insert. An unknown role_id raises 1452 (foreign key) the same way.
--   * status is always 'Active' on creation, matching the Django model default.
--
-- Apply locally:
--   mysql -h 127.0.0.1 -u worklink_dev -p worklink < data/procedures/sp_create_user.sql

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
        p_first_name,
        p_last_name,
        p_email,
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
        u.status
    FROM users AS u
    INNER JOIN roles AS r
        ON r.role_id = u.role_id
    WHERE u.user_id = v_user_id;
END$$

DELIMITER ;