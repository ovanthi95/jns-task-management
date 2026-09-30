"""API 09 POST and supporting GET /api/tasks/:taskId/comments."""

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from tasks.services.comment_create_service import (
    CommentTaskNotFound,
    create_task_comment,
    list_task_comments,
)
from ._session import not_authenticated, session_user


class CommentCreateSerializer(serializers.Serializer):
    comment_text = serializers.CharField(
        trim_whitespace=True,
        allow_blank=False,
        max_length=4000,
    )


@method_decorator(csrf_protect, name="dispatch")
class TaskCommentView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, task_id):
        actor = session_user(request)

        if actor is None:
            return not_authenticated()

        try:
            rows = list_task_comments(
                actor_user_id=actor["user_id"],
                task_id=task_id,
            )
        except CommentTaskNotFound:
            return Response(
                {"detail": "Not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(rows, status=status.HTTP_200_OK)

    def post(self, request, task_id):
        actor = session_user(request)

        if actor is None:
            return not_authenticated()

        serializer = CommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            comment = create_task_comment(
                actor_user_id=actor["user_id"],
                task_id=task_id,
                comment_text=serializer.validated_data["comment_text"],
            )
        except CommentTaskNotFound:
            return Response(
                {"detail": "Not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(comment, status=status.HTTP_201_CREATED)
