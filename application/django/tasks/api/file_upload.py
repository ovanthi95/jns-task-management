# API 10 - File upload
# Owner: Manatka
# POST /api/tasks/:taskId/files

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from tasks.services.file_upload_service import (
    FileUploadValidationError,
    StorageError,
    TaskNotAccessible,
    upload_task_file,
)
from ._session import not_authenticated, session_user


@method_decorator(csrf_protect, name="dispatch")
class FileUploadView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, task_id):
        user = session_user(request)

        if user is None:
            return not_authenticated()

        uploaded_file = request.FILES.get("file")

        if uploaded_file is None:
            return Response(
                {"file": ["No file was submitted."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            attachment = upload_task_file(
                user,
                task_id,
                uploaded_file,
            )
        except TaskNotAccessible:
            return Response(
                {"detail": "Not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except FileUploadValidationError as exc:
            return Response(
                exc.field_errors,
                status=status.HTTP_400_BAD_REQUEST,
            )
        except StorageError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(
            attachment,
            status=status.HTTP_201_CREATED,
        )
