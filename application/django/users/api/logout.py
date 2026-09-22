from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class LogoutView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        request.session.flush()

        return Response(
            {"message": "Logout successful."},
            status=status.HTTP_200_OK,
        )