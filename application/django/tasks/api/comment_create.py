"""API 09 - POST /api/tasks/:taskId/comments."""

from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from tasks.services.comment_create_service import (
    CommentTaskNotFound,
    create_task_comment,
)


class CommentCreateSerializer(serializers.Serializer):
    comment_text = serializers.CharField(
        trim_whitespace=True,
        allow_blank=False,
    )


class TaskCommentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, task_id):
        serializer = CommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            comment = create_task_comment(
                actor_user_id=request.user.user_id,
                task_id=task_id,
                comment_text=serializer.validated_data["comment_text"],
            )
        except CommentTaskNotFound:
            return Response(
                {"detail": "Not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(comment, status=status.HTTP_201_CREATED)
