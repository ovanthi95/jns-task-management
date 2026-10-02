"""Password management API endpoints.

Authenticated users can change their password. Unauthenticated users can
request a password-reset email and complete a reset using a one-time token.
"""

import os

from django.contrib.auth.hashers import check_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import User


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(write_only=True, trim_whitespace=False, min_length=8)
    confirm_password = serializers.CharField(write_only=True, trim_whitespace=False, min_length=8)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match."}
            )
        return attrs


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True, trim_whitespace=False, min_length=8)
    confirm_password = serializers.CharField(write_only=True, trim_whitespace=False, min_length=8)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match."}
            )
        return attrs


def _validate_new_password(password, user):
    try:
        validate_password(password, user=user)
    except ValidationError as exc:
        raise serializers.ValidationError({"new_password": list(exc.messages)}) from exc


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_id = request.session.get("user_id")
        user = User.objects.filter(user_id=user_id, status__iexact="Active").first()

        if user is None:
            request.session.flush()
            return Response(
                {"detail": "Not authenticated."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not check_password(
            serializer.validated_data["current_password"],
            user.password,
        ):
            return Response(
                {"current_password": "Current password is incorrect."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        new_password = serializer.validated_data["new_password"]

        if check_password(new_password, user.password):
            return Response(
                {"new_password": "New password must be different from the current password."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        _validate_new_password(new_password, user)

        user.set_password(new_password)
        user.save(update_fields=["password", "updated_at"])

        request.session.flush()

        return Response(
            {"message": "Password changed successfully. Please sign in again."},
            status=status.HTTP_200_OK,
        )


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"].strip().lower()
        user = User.objects.filter(
            email__iexact=email,
            status__iexact="Active",
        ).first()

        if user is not None:
            uid = urlsafe_base64_encode(force_bytes(user.user_id))
            token = default_token_generator.make_token(user)
            frontend_base = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000").rstrip("/")
            reset_url = f"{frontend_base}/reset-password/{uid}/{token}"

            send_mail(
                subject="Reset your Worklink password",
                message=(
                    "We received a request to reset your Worklink password.\n\n"
                    f"Use this link to choose a new password:\n{reset_url}\n\n"
                    "This link expires after the configured password-reset period. "
                    "If you did not request this, you can ignore this email."
                ),
                from_email=None,
                recipient_list=[user.email],
                fail_silently=False,
            )

        return Response(
            {"message": "If that email address belongs to an active Worklink user, a password reset link has been sent."},
            status=status.HTTP_200_OK,
        )


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, uidb64, token):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user_id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.filter(
                user_id=int(user_id),
                status__iexact="Active",
            ).first()
        except (TypeError, ValueError, OverflowError):
            user = None

        if user is None or not default_token_generator.check_token(user, token):
            return Response(
                {"detail": "This password reset link is invalid or has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        new_password = serializer.validated_data["new_password"]
        _validate_new_password(new_password, user)

        user.set_password(new_password)
        user.save(update_fields=["password", "updated_at"])

        return Response(
            {"message": "Password reset successfully. You can now sign in."},
            status=status.HTTP_200_OK,
        )
