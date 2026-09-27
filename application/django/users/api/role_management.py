"""API 14 - role and permission management."""

from django.db import IntegrityError, transaction
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import Permission, Role
from users.services.permission_service import (
    actor_has_permission,
    ensure_default_permissions,
    role_permission_codes,
    set_role_permissions,
)
from users.services.session_service import get_authenticated_session_user


class RoleWriteSerializer(serializers.Serializer):
    role_name = serializers.CharField(max_length=50, trim_whitespace=True, required=False)
    description = serializers.CharField(max_length=255, allow_blank=True, allow_null=True, required=False)
    is_active = serializers.BooleanField(required=False)
    permission_codes = serializers.ListField(
        child=serializers.CharField(max_length=80),
        required=False,
    )


def _actor(request):
    actor = get_authenticated_session_user(request.session.get("user_id"))
    if actor is None:
        request.session.flush()
    return actor


def _serialize_role(role):
    return {
        "role_id": role.role_id,
        "role_name": role.role_name,
        "description": role.description,
        "is_active": role.is_active,
        "is_protected": role.role_name.lower() == "admin",
        "permission_codes": sorted(role_permission_codes(role)),
    }


def _catalog():
    ensure_default_permissions()

    return [
        {
            "code": item.code,
            "label": item.label,
            "description": item.description,
            "category": item.category,
            "display_order": item.display_order,
        }
        for item in Permission.objects.filter(is_active=True).order_by(
            "category",
            "display_order",
            "label",
        )
    ]


@method_decorator(csrf_protect, name="dispatch")
class RoleListCreateView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        actor = _actor(request)

        if actor is None:
            return Response(
                {"detail": "Not authenticated."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        ensure_default_permissions()

        if not (
            actor_has_permission(actor, "manage_users")
            or actor_has_permission(actor, "manage_roles")
        ):
            return Response(
                {"detail": "Role access required."},
                status=status.HTTP_403_FORBIDDEN,
            )

        roles = Role.objects.prefetch_related(
            "role_permissions__permission"
        ).order_by("role_name")

        return Response({
            "permissions": _catalog(),
            "roles": [_serialize_role(role) for role in roles],
        })

    def post(self, request):
        actor = _actor(request)

        if actor is None:
            return Response(
                {"detail": "Not authenticated."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        ensure_default_permissions()

        if not actor_has_permission(actor, "manage_roles"):
            return Response(
                {"detail": "Role management permission required."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = RoleWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        role_name = str(data.get("role_name") or "").strip()

        if not role_name:
            return Response(
                {"role_name": ["Role name is required."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if role_name.lower() == "admin":
            return Response(
                {"role_name": ["Admin is a protected system role."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                role = Role.objects.create(
                    role_name=role_name,
                    description=data.get("description") or "",
                    is_active=data.get("is_active", True),
                    permissions_configured=True,
                )
                set_role_permissions(
                    role,
                    data.get("permission_codes", []),
                )
        except IntegrityError:
            return Response(
                {"role_name": ["A role with this name already exists."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except ValueError as exc:
            return Response(
                {"permission_codes": [str(exc)]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            _serialize_role(role),
            status=status.HTTP_201_CREATED,
        )


@method_decorator(csrf_protect, name="dispatch")
class RoleUpdateView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def patch(self, request, role_id):
        actor = _actor(request)

        if actor is None:
            return Response(
                {"detail": "Not authenticated."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        ensure_default_permissions()

        if not actor_has_permission(actor, "manage_roles"):
            return Response(
                {"detail": "Role management permission required."},
                status=status.HTTP_403_FORBIDDEN,
            )

        role = (
            Role.objects
            .prefetch_related("role_permissions__permission")
            .filter(role_id=role_id)
            .first()
        )

        if role is None:
            return Response(
                {"detail": "Role not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if role.role_name.lower() == "admin":
            return Response(
                {
                    "detail":
                        "Admin is a protected system role and cannot be modified."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = RoleWriteSerializer(
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if "role_name" in data:
            name = data["role_name"].strip()

            if not name:
                return Response(
                    {"role_name": ["Role name is required."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if name.lower() == "admin":
                return Response(
                    {"role_name": ["Admin is a protected system role."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            role.role_name = name

        if "description" in data:
            role.description = data["description"] or ""

        if "is_active" in data:
            if (
                not data["is_active"]
                and role.users.filter(status__iexact="Active").exists()
            ):
                return Response(
                    {
                        "is_active": [
                            "Move active users to another role before deactivating this role."
                        ]
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            role.is_active = data["is_active"]

        try:
            with transaction.atomic():
                role.save()

                if "permission_codes" in data:
                    set_role_permissions(
                        role,
                        data["permission_codes"],
                    )
        except IntegrityError:
            return Response(
                {"role_name": ["A role with this name already exists."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except ValueError as exc:
            return Response(
                {"permission_codes": [str(exc)]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(_serialize_role(role))
