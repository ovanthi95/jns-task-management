from data_access.users.get_session_user import get_session_user
from users.services.permission_service import actor_permission_codes


def get_authenticated_session_user(user_id):
    if not user_id:
        return None

    actor = get_session_user(user_id)
    if actor is None:
        return None

    actor = dict(actor)
    actor["permissions"] = sorted(actor_permission_codes(actor))
    return actor
