# API 04 - POST /api/projects
# Owner: Jessie

from django.db import DatabaseError
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from projects.services.project_create_service import (
    ProjectPermissionError,
    ProjectValidationError,
    create_project_service,
)
from users.services.session_service import get_authenticated_session_user


class ProjectCreateRequestSerializer(serializers.Serializer):
    project_name = serializers.CharField(
        max_length=150,
        allow_blank=False
    )

    description = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True
    )

    start_date = serializers.DateField(
        required=False,
        allow_null=True
    )

    end_date = serializers.DateField(
        required=False,
        allow_null=True
    )

    member_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )


class ProjectCreateView(APIView):

    def post(self, request):
        # Validate request body.
        serializer = ProjectCreateRequestSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        # Get the authenticated user from the Django session.
        user_id = request.session.get("user_id")

        if not user_id:
            return Response(
                {"detail": "Authentication required."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        current_user = get_authenticated_session_user(user_id)

        if current_user is None:
            return Response(
                {"detail": "Authentication required."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        data = serializer.validated_data

        try:
            project = create_project_service(
                current_user=current_user,
                project_name=data["project_name"],
                description=data.get("description"),
                start_date=data.get("start_date"),
                end_date=data.get("end_date"),
                member_ids=data.get("member_ids", [])
            )

        except ProjectPermissionError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_403_FORBIDDEN
            )

        except ProjectValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST
            )

        except DatabaseError:
            return Response(
                {"detail": "Unable to create project."},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {
                "message": "Project created successfully.",
                "project": project
            },
            status=status.HTTP_201_CREATED
        )