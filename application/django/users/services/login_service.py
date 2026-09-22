# API 01 - Login
# Owner: Ovanthi

from django.contrib.auth.hashers import check_password

from data_access.users.get_login_user import get_login_user


def authenticate_login(email, password):
    user = get_login_user(email)

    if user is None:
        return None

    password_hash = user.get("password_hash")

    if not password_hash:
        return None

    if not check_password(password, password_hash):
        return None

    user.pop("password_hash", None)

    return user