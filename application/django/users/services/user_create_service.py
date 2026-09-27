# API 03 - User create
# Owner: Manatka

from django.contrib.auth.hashers import make_password
from django.db import DatabaseError, IntegrityError, transaction

from data_access.users.create_user import create_user

USER_CREATE_ROLES = frozenset({"admin"})

MYSQL_DUPLICATE_ENTRY = 1062
MYSQL_FK_FAILS = 1452


class UserCreateValidationError(Exception):
    """A 400 with per-field messages, e.g. {"email": ["..."]}."""

    def __init__(self, field_errors):
        super().__init__("Validation failed")
        self.field_errors = field_errors


def can_create_user(session_user):
    role_name = (session_user or {}).get("role_name") or ""
    return role_name.lower() in USER_CREATE_ROLES


def create_user_in_organisation(session_user, data):
    """Create a user in the caller's organisation."""

    if not can_create_user(session_user):
        raise PermissionError("Your role is not permitted to create users.")

    email = data["email"].strip().lower()
    first_name = data["first_name"].strip()
    last_name = data["last_name"].strip()
    availability = (data.get("availability") or "").strip() or None
    password_hash = make_password(data["password"])

    try:
        with transaction.atomic():
            return create_user(
                organisation_id=session_user["organisation_id"],
                role_id=data["role_id"],
                first_name=first_name,
                last_name=last_name,
                email=email,
                password_hash=password_hash,
                availability=availability,
            )
    except IntegrityError as exc:
        code = exc.args[0] if exc.args else None

        if code == MYSQL_DUPLICATE_ENTRY:
            raise UserCreateValidationError(
                {"email": ["This email is already in use."]}
            ) from exc

        if code == MYSQL_FK_FAILS:
            raise UserCreateValidationError(
                {"role_id": ["Choose an active role."]}
            ) from exc

        raise
    except DatabaseError as exc:
        message = str(exc).lower()

        if "email already exists" in message:
            raise UserCreateValidationError(
                {"email": ["This email is already in use."]}
            ) from exc

        if "invalid role" in message:
            raise UserCreateValidationError(
                {"role_id": ["Choose an active role."]}
            ) from exc

        if "invalid organisation" in message:
            raise UserCreateValidationError(
                {"detail": ["Your organisation is not active."]}
            ) from exc

        raise
