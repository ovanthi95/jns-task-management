"""PATCH /api/projects/:projectId - project lifecycle and membership update."""

from django.db import DatabaseError
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from projects.services.project_update_service import (
    InvalidAdminPassword,
    ProjectNotFound,
    ReactivationPasswordRequired,
    edit_project,
)
from users.services.permission_service import actor_has_permission
from users.services.session_service import get_authenticated_session_user


class ProjectUpdateSerializer(serializers.Serializer):
    project_name = serializers.CharField(
        max_length=150,
        trim_whitespace=True,
        required=False,
    )
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )
    start_date = serializers.DateField(required=False, allow_null=True)
    end_date = serializers.DateField(required=False, allow_null=True)
    status = serializers.ChoiceField(
        choices=["Active", "Inactive", "Completed"],
        required=False,
    )
    member_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        allow_empty=True,
    )
    admin_password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=False,
        trim_whitespace=False,
    )

    def validate(self, attrs):
        editable_fields = set(attrs) - {"admin_password"}
        if not editable_fields:
            raise serializers.ValidationError(
                "Provide at least one field to update."
            )

        if "member_ids" in attrs:
            attrs["member_ids"] = list(dict.fromkeys(attrs["member_ids"]))

        return attrs


@method_decorator(csrf_protect, name="dispatch")
class ProjectUpdateView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def patch(self, request, project_id):
        actor = get_authenticated_session_user(request.session.get("user_id"))
        if actor is None:
            request.session.flush()
            return Response(
                {"detail": "Not authenticated."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not actor_has_permission(actor, "edit_projects"):
            return Response(
                {"detail": "Project editing permission required."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = ProjectUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        data = dict(serializer.validated_data)
        admin_password = data.pop("admin_password", None)

        try:
            project = edit_project(
                actor=actor,
                project_id=project_id,
                changes=data,
                admin_password=admin_password,
            )
        except ProjectNotFound:
            return Response(
                {"detail": "Project not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ReactivationPasswordRequired:
            return Response(
                {
                    "admin_password": [
                        "Your password is required to reopen a completed project."
                    ]
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except InvalidAdminPassword:
            return Response(
                {"admin_password": ["Incorrect password."]},
                status=status.HTTP_403_FORBIDDEN,
            )
        except DatabaseError as exc:
            message = str(exc).lower()

            if "end date cannot be before start date" in message:
                return Response(
                    {"end_date": ["End date cannot be before start date."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if "invalid project status" in message:
                return Response(
                    {"status": ["Choose Active, Inactive, or Completed."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if "project name is required" in message:
                return Response(
                    {"project_name": ["Project name is required."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if "project creator must remain a member" in message:
                return Response(
                    {"member_ids": ["The project creator must remain a member."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if "one or more project members are invalid or inactive" in message:
                return Response(
                    {
                        "member_ids": [
                            "One or more selected members are invalid or inactive."
                        ]
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            raise

        return Response(project)
