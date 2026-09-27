# API 03 - User create
# Owner: Manatka
# POST /api/users

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from users.services.session_service import get_authenticated_session_user
from users.services.user_create_service import (
    UserCreateValidationError,
    create_user_in_organisation,
)


class UserCreateRequestSerializer(serializers.Serializer):
    """Request shape only. organisation is deliberately absent."""

    first_name = serializers.CharField(max_length=80, trim_whitespace=True)
    last_name = serializers.CharField(max_length=80, trim_whitespace=True)
    email = serializers.EmailField(max_length=150)
    password = serializers.CharField(
        min_length=8,
        max_length=128,
        write_only=True,
        trim_whitespace=False,
    )
    role_id = serializers.IntegerField(min_value=1)
    availability = serializers.CharField(
        max_length=30,
        required=False,
        allow_blank=True,
        allow_null=True,
        trim_whitespace=True,
    )

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)
        return value


class UserCreateView(APIView):
    """401 no session, 403 not Admin, 400 field errors, 201 safe user fields."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        user_id = request.session.get("user_id")

        if not user_id:
            return Response(
                {"detail": "Not authenticated."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        session_user = get_authenticated_session_user(user_id)

        if session_user is None:
            request.session.flush()
            return Response(
                {"detail": "Not authenticated."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        serializer = UserCreateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = create_user_in_organisation(
                session_user,
                serializer.validated_data,
            )
        except PermissionError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_403_FORBIDDEN,
            )
        except UserCreateValidationError as exc:
            return Response(
                exc.field_errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(user, status=status.HTTP_201_CREATED)
