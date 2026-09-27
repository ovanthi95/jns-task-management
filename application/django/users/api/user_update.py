"""API 12 - PATCH /api/users/:userId."""

from django.db import DatabaseError, IntegrityError
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import Role
from users.services.session_service import get_authenticated_session_user
from users.services.user_update_service import edit_user


class UserUpdateSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=80, trim_whitespace=True, required=False)
    last_name = serializers.CharField(max_length=80, trim_whitespace=True, required=False)
    email = serializers.EmailField(max_length=150, required=False)
    role_name = serializers.CharField(max_length=50, required=False)
    availability = serializers.CharField(
        max_length=30,
        required=False,
        allow_blank=True,
        allow_null=True,
        trim_whitespace=True,
    )
    status = serializers.ChoiceField(
        choices=["Active", "Inactive"],
        required=False,
    )

    def validate_role_name(self, value):
        role = Role.objects.filter(
            role_name__iexact=value.strip(),
            is_active=True,
        ).first()

        if role is None:
            raise serializers.ValidationError("Choose an active role.")

        return role

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError(
                "Provide at least one field to update."
            )
        return attrs


@method_decorator(csrf_protect, name="dispatch")
class UserUpdateView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def patch(self, request, user_id):
        session_user = get_authenticated_session_user(
            request.session.get("user_id")
        )

        if session_user is None:
            request.session.flush()
            return Response(
                {"detail": "Not authenticated."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if str(session_user.get("role_name") or "").strip().lower() != "admin":
            return Response(
                {"detail": "Admin role required."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = UserUpdateSerializer(
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)

        data = dict(serializer.validated_data)
        role = data.pop("role_name", None)

        if role is not None:
            data["role_id"] = role.role_id

        is_self = int(user_id) == int(session_user["user_id"])

        if is_self and data.get("status") == "Inactive":
            return Response(
                {
                    "status": [
                        "You cannot deactivate the account you are currently signed in with."
                    ]
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            is_self
            and role is not None
            and role.role_id != session_user["role_id"]
        ):
            return Response(
                {
                    "role_name": [
                        "You cannot change the role of your own signed-in account."
                    ]
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if "email" in data:
            data["email"] = data["email"].strip().lower()

        try:
            updated = edit_user(
                organisation_id=session_user["organisation_id"],
                user_id=user_id,
                changes=data,
            )
        except IntegrityError as exc:
            if getattr(exc, "args", [None])[0] == 1062:
                return Response(
                    {"email": ["This email is already in use."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            raise
        except DatabaseError as exc:
            message = str(exc).lower()

            if "user not found" in message:
                return Response(
                    {"detail": "User not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            if "email already exists" in message:
                return Response(
                    {"email": ["This email is already in use."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if "invalid role" in message:
                return Response(
                    {"role_name": ["Choose an active role."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if "invalid user status" in message:
                return Response(
                    {"status": ["Choose Active or Inactive."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            raise

        return Response(updated, status=status.HTTP_200_OK)
