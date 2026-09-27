"""Shared helpers for writing readable central history records."""

from datetime import date, datetime
from decimal import Decimal

from audit.models import AuditLog


def json_safe(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, (date, datetime)):
        return value.isoformat()

    if isinstance(value, Decimal):
        return str(value)

    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}

    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]

    return str(value)


def record_history(
    *,
    organisation_id,
    user_id,
    entity_type,
    entity_id,
    entity_name,
    action,
    field_name=None,
    old_value=None,
    new_value=None,
    description=None,
):
    return AuditLog.objects.create(
        organisation_id=organisation_id,
        user_id=user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        entity_name=entity_name,
        action=action,
        field_name=field_name,
        description=description,
        old_value=json_safe(old_value),
        new_value=json_safe(new_value),
    )
