"""Serializers for API 02 and API 03.

    API 02  GET  /api/users   list users in the caller's organisation
    API 03  POST /api/users   create a user in the caller's organisation
"""

from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """API 02 output, and the body returned by API 03 after a create.

    The password hash is never included. organisation is omitted because a
    caller can only ever see their own organisation, so it carries no
    information.
    """

    role_name = serializers.CharField(source="role.role_name", read_only=True)

    class Meta:
        model = User
        fields = [
            "user_id",
            "first_name",
            "last_name",
            "email",
            "role_id",
            "role_name",
            "availability",
            "status",
        ]
        read_only_fields = fields