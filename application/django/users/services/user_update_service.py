"""API 12 user update application logic."""

from data_access.users.update_user import update_user


def edit_user(*, organisation_id, user_id, changes):
    return update_user(
        user_id=user_id,
        organisation_id=organisation_id,
        changes=changes,
    )
