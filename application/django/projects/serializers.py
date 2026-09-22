from django.db import transaction
from rest_framework import serializers

from users.models import User
from .models import Project, ProjectMember


class ProjectSerializer(serializers.ModelSerializer):
    """Read serializer for API 05 and the API 04 success response."""

    created_by_id = serializers.IntegerField(
        source="created_by.user_id",
        read_only=True,
    )

    class Meta:
        model = Project
        fields = [
            "project_id",
            "project_name",
            "description",
            "status",
            "start_date",
            "end_date",
            "created_by_id",
            "created_at",
            "updated_at",
        ]


class ProjectCreateSerializer(serializers.ModelSerializer):
    """Write serializer for API 04."""

    member_ids = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        many=True,
        write_only=True,
    )

    class Meta:
        model = Project
        fields = [
            "project_name",
            "description",
            "status",
            "start_date",
            "end_date",
            "member_ids",
        ]

    def validate_project_name(self, value):
        """Reject a project name that contains only whitespace."""

        project_name = value.strip()

        if not project_name:
            raise serializers.ValidationError(
                "Project name cannot be blank."
            )

        return project_name

    def validate(self, attrs):
        """Validate project dates and selected members."""

        start_date = attrs.get("start_date")
        end_date = attrs.get("end_date")

        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError(
                {
                    "end_date":
                    "End date cannot be before the start date."
                }
            )

        members = attrs.get("member_ids", [])
        request = self.context.get("request")

        if request:
            for member in members:
                if member.organisation_id != request.user.organisation_id:
                    raise serializers.ValidationError(
                        {
                            "member_ids":
                            "All members must belong to your organisation."
                        }
                    )

        return attrs

    def create(self, validated_data):
        """Create the project and its memberships as one transaction."""

        members = validated_data.pop("member_ids")
        request = self.context["request"]
        creator = request.user

        with transaction.atomic():
            project = Project.objects.create(
                organisation=creator.organisation,
                created_by=creator,
                **validated_data,
            )

            # The creator must be an explicit project member because the
            # existing task APIs do not treat created_by as membership.
            ProjectMember.objects.create(
                project=project,
                user=creator,
            )

            # Avoid creating a duplicate membership if the creator was also
            # supplied in member_ids.
            for member in members:
                if member.pk != creator.pk:
                    ProjectMember.objects.get_or_create(
                        project=project,
                        user=member,
                    )

        return project