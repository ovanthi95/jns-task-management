# API 10 - File upload
# Owner: Manatka
# POST /api/tasks/:taskId/files  (multipart/form-data, field name "file")

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
from users.services.session_service import get_authenticated_session_user


class FileUploadView(APIView):
    """401 no session, 404 task not accessible, 400 bad file, 502 storage
    failure, 201 with the attachment metadata."""

    authentication_classes = []
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, task_id):
        user_id = request.session.get("user_id")

        if not user_id:
            return Response({"detail": "Not authenticated."},
                            status=status.HTTP_401_UNAUTHORIZED)

        session_user = get_authenticated_session_user(user_id)

        if session_user is None:
            request.session.flush()
            return Response({"detail": "Not authenticated."},
                            status=status.HTTP_401_UNAUTHORIZED)

        uploaded_file = request.FILES.get("file")

        if uploaded_file is None:
            return Response({"file": ["No file was submitted."]},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            attachment = upload_task_file(session_user, task_id, uploaded_file)
        except TaskNotAccessible:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        except FileUploadValidationError as exc:
            return Response(exc.field_errors, status=status.HTTP_400_BAD_REQUEST)
        except StorageError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        return Response(attachment, status=status.HTTP_201_CREATED)