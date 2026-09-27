"""Focused tests for API 14 - role management."""

from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from users.models import Role


def actor(*permissions):
    return {
        "user_id": 1,
        "organisation_id": 1,
        "role_id": 1,
        "role_name": "Admin",
        "first_name": "Admin",
        "last_name": "User",
        "email": "admin@example.com",
        "permissions": list(permissions),
    }


class RoleManagementApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    @patch("users.api.role_management.get_authenticated_session_user", return_value=None)
    def test_unauthenticated_roles_returns_401(self, _actor):
        response = self.client.get("/api/roles")
        self.assertEqual(response.status_code, 401)

    @patch("users.api.role_management.get_authenticated_session_user")
    def test_get_roles_with_manage_users_returns_200(self, get_actor):
        get_actor.return_value = actor("manage_users")
        response = self.client.get("/api/roles")
        self.assertEqual(response.status_code, 200)
        self.assertIn("roles", response.data)
        self.assertIn("permissions", response.data)

    @patch("users.api.role_management.get_authenticated_session_user")
    def test_create_role_with_manage_roles_persists(self, get_actor):
        get_actor.return_value = actor("manage_roles")
        response = self.client.post(
            "/api/roles",
            {
                "role_name": "Reviewer",
                "description": "Review access",
                "permission_codes": [],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Role.objects.filter(role_name="Reviewer").exists())

    @patch("users.api.role_management.get_authenticated_session_user")
    def test_protected_admin_name_cannot_be_created(self, get_actor):
        get_actor.return_value = actor("manage_roles")
        response = self.client.post(
            "/api/roles",
            {"role_name": "Admin", "permission_codes": []},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    @patch("users.api.role_management.get_authenticated_session_user")
    def test_unknown_role_returns_404(self, get_actor):
        get_actor.return_value = actor("manage_roles")
        response = self.client.patch(
            "/api/roles/999999",
            {"description": "Changed"},
            format="json",
        )
        self.assertEqual(response.status_code, 404)
