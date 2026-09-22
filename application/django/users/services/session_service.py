from data_access.users.get_session_user import get_session_user


def get_authenticated_session_user(user_id):
    if not user_id:
        return None

    return get_session_user(user_id)