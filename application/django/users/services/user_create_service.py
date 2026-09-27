# API 03 - User create
# Owner: Manatka

from django.contrib.auth.hashers import make_password
from django.db import IntegrityError, transaction

from audit.services.history_recording import record_history
from data_access.users.create_user import create_user
from users.services.permission_service import actor_has_permission

# MySQL error numbers surfaced through IntegrityError.args[0]
MYSQL_DUPLICATE_ENTRY = 1062
MYSQL_FK_FAILS = 1452


class UserCreateValidationError(Exception):
    """A 400 with per-field messages, e.g. {"email": ["..."]}."""

    def __init__(self, field_errors):
        super().__init__("Validation failed")
        self.field_errors = field_errors


def can_create_user(session_user):
    return actor_has_permission(session_user, "manage_users")


def create_user_in_organisation(session_user, data):
    """Create a user in the caller's organisation.

    - organisation_id comes from the session user, never from `data`.
    - The plain password is hashed here; only the hash reaches the procedure.
    - Duplicate (organisation, email) and unknown role become field errors,
      without exposing SQL text. The insert runs in a savepoint so a failed
      insert cannot poison the surrounding transaction.
    """

    if not can_create_user(session_user):
        raise PermissionError("Your role is not permitted to create users.")

    password_hash = make_password(data["password"])

    try:
        with transaction.atomic():
            created = create_user(
                organisation_id=session_user["organisation_id"],
                role_id=data["role_id"],
                first_name=data["first_name"],
                last_name=data["last_name"],
                email=data["email"].strip().lower(),
                password_hash=password_hash,
                availability=data.get("availability") or None,
            )

            entity_name = (
                f"{created['first_name']} {created['last_name']}"
            ).strip()

            record_history(
                organisation_id=session_user["organisation_id"],
                user_id=session_user["user_id"],
                entity_type="User",
                entity_id=created["user_id"],
                entity_name=entity_name,
                action="Created",
                new_value={
                    "name": entity_name,
                    "email": created["email"],
                    "role": created["role_name"],
                    "status": created["status"],
                },
                description=f'Created user "{entity_name}".',
            )

            return created
    except IntegrityError as exc:
        code = exc.args[0] if exc.args else None

        if code == MYSQL_DUPLICATE_ENTRY:
            raise UserCreateValidationError(
                {"email": ["A user with this email already exists in your organisation."]}
            ) from exc

        if code == MYSQL_FK_FAILS:
            raise UserCreateValidationError(
                {"role_id": ["Unknown role."]}
            ) from exc

        raise