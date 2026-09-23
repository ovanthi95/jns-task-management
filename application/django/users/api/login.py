# API 01 - Login
# Owner: Ovanthi
# POST /api/auth/login

from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from users.services.login_service import authenticate_login


class LoginRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False
    )


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = LoginRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        user = authenticate_login(email, password)

        if user is None:
            return Response(
                {"detail": "Invalid email or password."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Create a fresh session for the authenticated user
        request.session.cycle_key()
        request.session["user_id"] = user["user_id"]

        return Response(
            {
                "message": "Login successful.",
                "user": user
            },
            status=status.HTTP_200_OK
        )