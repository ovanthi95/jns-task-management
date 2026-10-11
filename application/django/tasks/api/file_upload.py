# API 10 POST and supporting GET /api/tasks/:taskId/files

from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from data_access.tasks.get_task_access import get_task_access
from data_access.tasks.get_task_files import get_task_file, get_task_files
from tasks.services.file_upload_service import (
    FileUploadValidationError,
    StorageError,
    TaskNotAccessible,
    upload_task_file,
)
from users.services.session_service import get_authenticated_session_user


class FileUploadView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def _session_user(self, request):
        user_id = request.session.get("user_id")
        if not user_id:
            return None

        session_user = get_authenticated_session_user(user_id)
        if session_user is None:
            request.session.flush()
            return None

        return session_user

    def get(self, request, task_id):
        session_user = self._session_user(request)
        if session_user is None:
            return Response(
                {"detail": "Not authenticated."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        task = get_task_access(task_id, session_user["user_id"])
        if task is None:
            return Response(
                {"detail": "Not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        files = get_task_files(task_id)
        return Response(
            [
                {key: value for key, value in file.items() if key != "s3_key"}
                for file in files
            ],
            status=status.HTTP_200_OK,
        )

    def post(self, request, task_id):
        session_user = self._session_user(request)
        if session_user is None:
            return Response(
                {"detail": "Not authenticated."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        uploaded_file = request.FILES.get("file")

        if uploaded_file is None:
            return Response(
                {"file": ["No file was submitted."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            attachment = upload_task_file(
                session_user,
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

        return Response(attachment, status=status.HTTP_201_CREATED)
