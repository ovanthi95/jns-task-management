# API 04 - POST /api/projects
# Owner: Jessie

from django.db import DatabaseError

from audit.models import AuditLog
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
        allow_blank=False,
        trim_whitespace=True,
    )
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        trim_whitespace=True,
    )
    start_date = serializers.DateField(required=False, allow_null=True)
    end_date = serializers.DateField(required=False, allow_null=True)
    member_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        allow_empty=True,
    )

    def validate(self, attrs):
        start_date = attrs.get("start_date")
        end_date = attrs.get("end_date")

        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError({
                "end_date": ["End date cannot be before start date."]
            })

        return attrs


class ProjectCreateView(APIView):

    def post(self, request):
        serializer = ProjectCreateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_id = request.session.get("user_id")

        if not user_id:
            return Response(
                {"detail": "Authentication required."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        current_user = get_authenticated_session_user(user_id)

        if current_user is None:
            request.session.flush()
            return Response(
                {"detail": "Authentication required."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        data = serializer.validated_data

        try:
            project = create_project_service(
                current_user=current_user,
                project_name=data["project_name"],
                description=data.get("description"),
                start_date=data.get("start_date"),
                end_date=data.get("end_date"),
                member_ids=data.get("member_ids", []),
            )
        except ProjectPermissionError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_403_FORBIDDEN,
            )
        except ProjectValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except DatabaseError as exc:
            message = str(exc).lower()

            if "project name is required" in message:
                return Response(
                    {"project_name": ["Project name is required."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if "end date cannot be before start date" in message:
                return Response(
                    {"end_date": ["End date cannot be before start date."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if "invalid or inactive" in message:
                return Response(
                    {"member_ids": ["One or more project members are invalid or inactive."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            return Response(
                {"detail": "Unable to create project."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        AuditLog.objects.create(
            organisation_id=current_user["organisation_id"],
            user_id=current_user["user_id"],
            action="Created",
            entity_type="Project",
            entity_id=project["project_id"],
            entity_name=project["project_name"],
            description="Project created.",
            new_value={
                "status": project.get("status"),
                "start_date": str(project.get("start_date") or ""),
                "end_date": str(project.get("end_date") or ""),
            },
        )

        return Response(project, status=status.HTTP_201_CREATED)
